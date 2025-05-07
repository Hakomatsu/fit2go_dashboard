import json
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from ..models import DataPoint, FitnessSession, db

bp = Blueprint("api", __name__)


@bp.before_request
def verify_token():
    """APIトークンの検証"""
    # 開発環境では特定のエンドポイントの認証をスキップ
    if current_app.config["ENV"] == "development":
        if request.endpoint in ["api.receive_data", "api.download_data"]:
            return None
        
    token = request.headers.get("X-API-Token")
    if not token or token != current_app.config["API_TOKEN"]:
        return jsonify({"error": "Invalid API token"}), 401


@bp.route("/data", methods=["POST"])
def receive_data():
    """M5Stackからのデータ受信"""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    try:
        data = request.get_json()
        device_id = data.get("device_id")
        if not device_id:
            return jsonify({"error": "device_id is required"}), 400

        # アクティブなセッションを取得または新規作成
        session = FitnessSession.query.filter_by(device_id=device_id, end_time=None).first()

        if not session:
            session = FitnessSession(
                device_id=device_id,
                start_time=datetime.utcnow(),
                total_time_seconds=data.get("total_time_s", 0),
                total_distance_km=data.get("total_dist_km", 0.0),
                total_calories_kcal=data.get("total_cal_kcal", 0.0),
                average_speed_kmh=data.get("speed_kmh", 0.0),
                average_rpm=data.get("rpm", 0.0),
                average_mets=data.get("mets", 0.0),
                raw_data=data
            )
            db.session.add(session)
            # セッションを即時コミットしてIDを取得
            db.session.flush()

        # データポイントの作成
        timestamp = datetime.utcnow()
        if "timestamp_ms" in data:
            try:
                # UNIXタイムスタンプ（ミリ秒）をdatetimeに変換
                timestamp = datetime.fromtimestamp(data["timestamp_ms"] / 1000.0)
            except (ValueError, TypeError):
                pass  # タイムスタンプの変換に失敗した場合は現在時刻を使用

        data_point = DataPoint(
            session_id=session.id,
            timestamp=timestamp,
            speed_kmh=data.get("speed_kmh", 0.0),
            rpm=data.get("rpm", 0.0),
            distance_km=data.get("session_dist_km", 0.0),
            calories_kcal=data.get("session_cal_kcal", 0.0),
            time_seconds=int(data.get("session_time_s", 0)),
            mets=data.get("mets", 0.0)
        )
        db.session.add(data_point)

        # セッションデータの更新
        session.total_time_seconds = data.get("total_time_s", session.total_time_seconds)
        session.total_distance_km = data.get("total_dist_km", session.total_distance_km)
        session.total_calories_kcal = data.get("total_cal_kcal", session.total_calories_kcal)
        session.average_speed_kmh = data.get("speed_kmh", session.average_speed_kmh)
        session.average_rpm = data.get("rpm", session.average_rpm)
        session.average_mets = data.get("mets", session.average_mets)
        session.raw_data = data

        db.session.commit()
        return jsonify({"status": "success", "session_id": session.id}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/upload", methods=["POST"])
def upload_data():
    """SDカードのデータをアップロード"""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()
    device_id = data.get("device_id")
    sessions = data.get("sessions", [])

    if not device_id or not sessions:
        return jsonify({"error": "device_id and sessions are required"}), 400

    results = []
    for session_data in sessions:
        try:
            # セッションの作成または更新
            session = FitnessSession(
                device_id=device_id,
                start_time=datetime.fromisoformat(session_data.get("start_time")),
                end_time=datetime.fromisoformat(session_data.get("end_time")),
                total_time_seconds=session_data.get("total_time_seconds", 0),
                total_distance_km=session_data.get("total_distance_km", 0.0),
                total_calories_kcal=session_data.get("total_calories_kcal", 0.0),
                average_speed_kmh=session_data.get("average_speed_kmh", 0.0),
                average_rpm=session_data.get("average_rpm", 0.0),
                average_mets=session_data.get("average_mets", 0.0),
                raw_data=session_data,
            )
            db.session.add(session)
            db.session.flush()  # セッションIDを取得するためにフラッシュ

            # データポイントの作成
            for point_data in session_data.get("data_points", []):
                data_point = DataPoint(
                    session_id=session.id,
                    timestamp=datetime.fromisoformat(point_data.get("timestamp")),
                    speed_kmh=point_data.get("speed_kmh", 0.0),
                    rpm=point_data.get("rpm", 0.0),
                    distance_km=point_data.get("distance_km", 0.0),
                    calories_kcal=point_data.get("calories_kcal", 0.0),
                    time_seconds=point_data.get("time_seconds", 0),
                    mets=point_data.get("mets", 0.0),
                )
                db.session.add(data_point)

            results.append(
                {
                    "status": "success",
                    "session_id": session.id,
                    "start_time": session.start_time.isoformat(),
                }
            )
        except Exception as e:
            results.append(
                {
                    "status": "error",
                    "error": str(e),
                    "start_time": session_data.get("start_time"),
                }
            )

    try:
        db.session.commit()
        return jsonify({"status": "success", "results": results}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# app/routes/api.pyに追加


@bp.route("/download", methods=["GET"])
def download_data():
    """フィットネスデータをダウンロードするためのエンドポイント"""
    import json
    import os
    import tempfile
    from datetime import datetime, time, timedelta
    import pandas as pd
    from flask import send_file, make_response

    # クエリパラメータの取得
    format_type = request.args.get("format", "json")
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    device_id = request.args.get("device_id")

    # 日付バリデーション
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            start_date = datetime.combine(start_date.date(), time.min)
        else:
            start_date = datetime.now() - timedelta(days=30)
            start_date = datetime.combine(start_date.date(), time.min)

        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            end_date = datetime.combine(end_date.date(), time.max)
        else:
            end_date = datetime.now()
            end_date = datetime.combine(end_date.date(), time.max)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # クエリ構築とデータ取得
    query = FitnessSession.query.filter(
        FitnessSession.start_time.between(start_date, end_date)
    )
    if device_id:
        query = query.filter(FitnessSession.device_id == device_id)
    sessions = query.all()

    # データの準備
    result = []
    for session in sessions:
        session_data = {
            "id": session.id,
            "device_id": session.device_id,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "total_time_seconds": session.total_time_seconds,
            "total_distance_km": session.total_distance_km,
            "total_calories_kcal": session.total_calories_kcal,
            "average_speed_kmh": session.average_speed_kmh,
            "average_rpm": session.average_rpm,
            "average_mets": session.average_mets,
            "data_points": [],
        }

        data_points = (
            DataPoint.query.filter_by(session_id=session.id)
            .order_by(DataPoint.timestamp)
            .all()
        )

        for point in data_points:
            point_data = {
                "timestamp": point.timestamp.isoformat(),
                "speed_kmh": point.speed_kmh,
                "rpm": point.rpm,
                "distance_km": point.distance_km,
                "calories_kcal": point.calories_kcal,
                "time_seconds": point.time_seconds,
                "mets": point.mets,
            }
            session_data["data_points"].append(point_data)

        result.append(session_data)

    if format_type.lower() == "json":
        # JSONとして返す
        response = make_response(jsonify(result))
        response.headers["Content-Disposition"] = "attachment; filename=fitness_data.json"
        return response

    elif format_type.lower() == "csv":
        # セッションデータをDataFrameに変換
        sessions_data = []
        points_data = []
        
        for s in result:
            sessions_data.append({
                "session_id": s["id"],
                "device_id": s["device_id"],
                "start_time": s["start_time"],
                "end_time": s["end_time"],
                "total_time_seconds": s["total_time_seconds"],
                "total_distance_km": s["total_distance_km"],
                "total_calories_kcal": s["total_calories_kcal"],
                "average_speed_kmh": s["average_speed_kmh"],
                "average_rpm": s["average_rpm"],
                "average_mets": s["average_mets"],
            })
            
            for p in s["data_points"]:
                points_data.append({
                    "session_id": s["id"],
                    "timestamp": p["timestamp"],
                    "speed_kmh": p["speed_kmh"],
                    "rpm": p["rpm"],
                    "distance_km": p["distance_km"],
                    "calories_kcal": p["calories_kcal"],
                    "time_seconds": p["time_seconds"],
                    "mets": p["mets"],
                })

        sessions_df = pd.DataFrame(sessions_data)
        points_df = pd.DataFrame(points_data) if points_data else pd.DataFrame()

        # 一時ファイルを作成
        temp_dir = tempfile.mkdtemp()
        try:
            sessions_file = os.path.join(temp_dir, "sessions.csv")
            points_file = os.path.join(temp_dir, "data_points.csv")
            zip_file = os.path.join(temp_dir, "fitness_data.zip")

            # CSVファイルを保存
            sessions_df.to_csv(sessions_file, index=False)
            if not points_df.empty:
                points_df.to_csv(points_file, index=False)

            # ZIPファイルに圧縮
            import zipfile
            with zipfile.ZipFile(zip_file, "w") as zipf:
                zipf.write(sessions_file, arcname="sessions.csv")
                if not points_df.empty:
                    zipf.write(points_file, arcname="data_points.csv")

            return send_file(
                zip_file,
                mimetype="application/zip",
                as_attachment=True,
                download_name="fitness_data.zip"
            )

        finally:
            # 一時ファイルの削除を試みる（エラーは無視）
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

    else:
        return jsonify({"error": 'Unsupported format. Use "json" or "csv"'}), 400


@bp.route("/sessions/<int:session_id>/end", methods=["POST"])
def end_session(session_id):
    """セッションを終了し、必要に応じてヘルスサービスと同期"""
    from ..services.google_fit import end_fitness_session

    auto_sync = request.args.get("auto_sync", "true").lower() == "true"
    result = end_fitness_session(session_id, auto_sync=auto_sync)

    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify({"error": result["error"]}), 400


@bp.route("/sessions/<int:session_id>/sync", methods=["POST"])
def sync_session(session_id):
    """セッションを手動でヘルスサービスと同期"""
    from ..services.google_fit import sync_session_to_services

    result = sync_session_to_services(session_id)
    return jsonify(result), 200 if any(r["success"] for r in result.values()) else 400


@bp.route("/sessions/<int:session_id>", methods=["GET"])
def get_session(session_id):
    """特定のセッションの詳細を取得"""
    session = FitnessSession.query.get_or_404(session_id)
    
    # データポイントを取得
    data_points = (
        DataPoint.query.filter_by(session_id=session_id)
        .order_by(DataPoint.timestamp)
        .all()
    )

    session_data = {
        "id": session.id,
        "device_id": session.device_id,
        "start_time": session.start_time.isoformat(),
        "end_time": session.end_time.isoformat() if session.end_time else None,
        "total_time_seconds": session.total_time_seconds,
        "total_distance_km": session.total_distance_km,
        "total_calories_kcal": session.total_calories_kcal,
        "average_speed_kmh": session.average_speed_kmh,
        "average_rpm": session.average_rpm,
        "average_mets": session.average_mets,
        "raw_data": session.raw_data,
        "data_points": [
            {
                "timestamp": point.timestamp.isoformat(),
                "speed_kmh": point.speed_kmh,
                "rpm": point.rpm,
                "distance_km": point.distance_km,
                "calories_kcal": point.calories_kcal,
                "time_seconds": point.time_seconds,
                "mets": point.mets
            }
            for point in data_points
        ]
    }

    return jsonify(session_data)


@bp.route("/api/sessions/current")
def get_current_session():
    """現在進行中のセッションデータを取得"""
    session = FitnessSession.query.filter_by(end_time=None).first()
    if not session:
        return jsonify({"status": "no_active_session"})

    # 最新のデータポイントを取得
    latest_point = (
        DataPoint.query.filter_by(session_id=session.id)
        .order_by(DataPoint.timestamp.desc())
        .first()
    )

    response_data = {
        "session_id": session.id,
        "start_time": session.start_time.isoformat(),
        "total_time_seconds": session.total_time_seconds,
        "total_distance_km": session.total_distance_km,
        "total_calories_kcal": session.total_calories_kcal,
        "current_speed_kmh": latest_point.speed_kmh if latest_point else 0,
        "current_rpm": latest_point.rpm if latest_point else 0,
        "current_mets": latest_point.mets if latest_point else 0,
        "session_time_s": latest_point.time_seconds if latest_point else 0,
        "session_dist_km": latest_point.distance_km if latest_point else 0,
        "session_cal_kcal": latest_point.calories_kcal if latest_point else 0
    }

    print("\n=== Dashboard Metrics ===")
    print("Session Distance:", response_data["session_dist_km"], "km")
    print("Session Calories:", response_data["session_cal_kcal"], "kcal")
    print("Session Time:", response_data["session_time_s"], "seconds")
    print("Total Distance:", response_data["total_distance_km"], "km")
    print("Total Calories:", response_data["total_calories_kcal"], "kcal")
    print("Total Time:", response_data["total_time_seconds"], "seconds")
    print("======================\n")

    return jsonify(response_data)
