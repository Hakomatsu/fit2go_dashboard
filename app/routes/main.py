import json
from datetime import datetime, timedelta

import pytz
from flask import Blueprint, current_app, jsonify, render_template, request, redirect, url_for
from sqlalchemy import func

from ..models import DataPoint, FitnessSession, db
from ..services.google_fit import (
    get_authorization_url,
    handle_callback,
    upload_fitness_session,
)

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """ダッシュボードのメインページを表示"""
    return render_template("index.html")


@bp.route("/calendar")
def calendar():
    """カレンダービューを表示"""
    return render_template("calendar.html")


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

    return jsonify(
        {
            "session_id": session.id,
            "start_time": session.start_time.isoformat(),
            "total_time_seconds": session.total_time_seconds,
            "total_distance_km": session.total_distance_km,
            "total_calories_kcal": session.total_calories_kcal,
            "current_speed_kmh": latest_point.speed_kmh if latest_point else 0,
            "current_rpm": latest_point.rpm if latest_point else 0,
            "current_mets": latest_point.mets if latest_point else 0,
            # セッションの現在の値を追加
            "session_time_s": latest_point.time_seconds if latest_point else 0,
            "session_dist_km": latest_point.distance_km if latest_point else 0,
            "session_cal_kcal": latest_point.calories_kcal if latest_point else 0
        }
    )


@bp.route("/api/sessions/daily")
def get_daily_stats():
    """指定された日の統計データを取得"""
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    # 指定された日の期間を設定
    start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=1)

    # 15分単位でデータを集計
    interval = 15  # minutes
    stats = []
    
    # 24時間分の15分間隔のデータを生成
    for hour in range(24):
        for minute in range(0, 60, interval):
            interval_start = start_time + timedelta(hours=hour, minutes=minute)
            interval_end = interval_start + timedelta(minutes=interval)
            
            # 各時間間隔のデータを集計
            data = (
                db.session.query(
                    func.avg(DataPoint.speed_kmh).label("avg_speed"),
                    func.avg(DataPoint.rpm).label("avg_rpm"),
                    func.sum(DataPoint.distance_km).label("total_distance"),
                    func.sum(DataPoint.calories_kcal).label("total_calories"),
                    func.count(DataPoint.id).label("point_count"),
                )
                .filter(DataPoint.timestamp >= interval_start)
                .filter(DataPoint.timestamp < interval_end)
                .first()
            )
            
            stats.append({
                "time": interval_start.isoformat(),
                "avg_speed": float(data.avg_speed) if data.avg_speed else 0,
                "avg_rpm": float(data.avg_rpm) if data.avg_rpm else 0,
                "total_distance": float(data.total_distance) if data.total_distance else 0,
                "total_calories": float(data.total_calories) if data.total_calories else 0,
                "point_count": data.point_count,
            })

    return jsonify(stats)


@bp.route("/api/sessions/cumulative")
def get_cumulative_stats():
    """累積統計データを取得"""
    stats = db.session.query(
        func.sum(FitnessSession.total_time_seconds).label("total_time"),
        func.sum(FitnessSession.total_distance_km).label("total_distance"),
        func.sum(FitnessSession.total_calories_kcal).label("total_calories"),
    ).first()

    return jsonify(
        {
            "total_time_seconds": int(stats.total_time) if stats.total_time else 0,
            "total_distance_km": float(stats.total_distance)
            if stats.total_distance
            else 0,
            "total_calories_kcal": float(stats.total_calories)
            if stats.total_calories
            else 0,
        }
    )


@bp.route("/connect/google-fit")
def connect_google_fit():
    """Google Fitとの連携を開始"""
    # 認証URLを取得してリダイレクト
    auth_url = get_authorization_url()
    return redirect(auth_url)


@bp.route("/google-fit/callback")
def google_fit_callback():
    """Google Fit認証コールバック"""
    try:
        # コールバックを処理
        handle_callback(request)
        return redirect(url_for("main.index", status="connected"))
    except Exception as e:
        current_app.logger.error(f"Google Fit認証エラー: {str(e)}")
        return redirect(url_for("main.index", status="error"))


@bp.route("/api/sessions/<int:session_id>/share/google-fit", methods=["POST"])
def share_to_google_fit(session_id):
    """特定のセッションをGoogle Fitに共有"""
    try:
        result = upload_fitness_session(session_id)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Google Fitへのデータ共有エラー: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/calendar/fit2go")
def get_fit2go_calendar_data():
    """カレンダー表示用のFit2Goセッションデータを取得"""
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    try:
        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return jsonify({"error": "Invalid date format"}), 400

    # セッションデータを取得
    sessions = FitnessSession.query.filter(
        FitnessSession.start_time.between(start, end)
    ).all()

    events = []
    for session in sessions:
        events.append({
            "id": session.id,
            "title": f"Exercise ({session.total_distance_km:.1f}km)",
            "start": session.start_time.isoformat(),
            "end": session.end_time.isoformat() if session.end_time else None,
            "extendedProps": {
                "distance": session.total_distance_km,
                "calories": session.total_calories_kcal,
                "duration": session.total_time_seconds,
                "avg_speed": session.average_speed_kmh,
                "avg_rpm": session.average_rpm,
                "avg_mets": session.average_mets,
            }
        })

    return jsonify(events)


@bp.route("/api/calendar/googlefit")
def get_googlefit_calendar_data():
    """カレンダー表示用のGoogle Fitデータを取得"""
    # 現在は未実装のため、空のリストを返す
    return jsonify([])


@bp.route("/api/calendar/healthconnect")
def get_healthconnect_calendar_data():
    """カレンダー表示用のHealth Connectデータを取得"""
    # 現在は未実装のため、空のリストを返す
    return jsonify([])


@bp.route("/api/daily/<source>/<date>")
def get_daily_source_data(source, date):
    """特定のソースの日次データを取得"""
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=1)

    if source == "fit2go":
        # Fit2Goのデータを取得
        sessions = FitnessSession.query.filter(
            FitnessSession.start_time.between(start_time, end_time)
        ).all()

        daily_data = {
            "total_time_seconds": sum(s.total_time_seconds or 0 for s in sessions),
            "total_distance_km": sum(s.total_distance_km or 0 for s in sessions),
            "total_calories_kcal": sum(s.total_calories_kcal or 0 for s in sessions),
            "sessions": [
                {
                    "id": s.id,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat() if s.end_time else None,
                    "duration": s.total_time_seconds,
                    "distance": s.total_distance_km,
                    "calories": s.total_calories_kcal,
                    "avg_speed": s.average_speed_kmh,
                    "avg_rpm": s.average_rpm,
                    "avg_mets": s.average_mets,
                }
                for s in sessions
            ],
        }
        return jsonify(daily_data)

    elif source == "googlefit":
        # Google Fitのデータは現在未実装
        return jsonify({
            "total_time_seconds": 0,
            "total_distance_km": 0,
            "total_calories_kcal": 0,
            "sessions": []
        })

    elif source == "healthconnect":
        # Health Connectのデータは現在未実装
        return jsonify({
            "total_time_seconds": 0,
            "total_distance_km": 0,
            "total_calories_kcal": 0,
            "sessions": []
        })

    else:
        return jsonify({"error": "Invalid source"}), 400


@bp.route("/api/sessions/history")
def get_session_history():
    """直近30分間のセッションデータを取得"""
    # 現在のアクティブセッションを取得
    session = FitnessSession.query.filter_by(end_time=None).first()
    if not session:
        return jsonify([])

    # 現在時刻から30分前までのデータを取得
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=30)

    data_points = (
        DataPoint.query.filter_by(session_id=session.id)
        .filter(DataPoint.timestamp >= start_time)
        .filter(DataPoint.timestamp <= end_time)
        .order_by(DataPoint.timestamp.asc())
        .all()
    )

    return jsonify([
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
    ])
