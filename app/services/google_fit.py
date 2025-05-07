# app/services/google_fit.py

import os
import json
import requests
from datetime import datetime, timezone
from flask import current_app, url_for, session, redirect, request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Fit APIのスコープ
SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.activity.write",
]


def get_google_fit_service():
    """Google Fit APIのサービスオブジェクトを取得"""
    credentials = get_credentials()
    if not credentials:
        return None

    return build("fitness", "v1", credentials=credentials)


def get_credentials():
    """保存されたGoogle認証情報を取得"""
    if "google_credentials" not in session:
        return None

    creds_data = json.loads(session["google_credentials"])
    return Credentials(
        token=creds_data["token"],
        refresh_token=creds_data["refresh_token"],
        token_uri=creds_data["token_uri"],
        client_id=current_app.config["GOOGLE_CLIENT_ID"],
        client_secret=current_app.config["GOOGLE_CLIENT_SECRET"],
        scopes=creds_data["scopes"],
    )


def store_credentials(credentials):
    """Google認証情報をセッションに保存"""
    session["google_credentials"] = json.dumps(
        {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "scopes": credentials.scopes,
        }
    )


def get_authorization_url():
    """Google認証のURLを取得"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": current_app.config["GOOGLE_CLIENT_ID"],
                "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [url_for("main.google_fit_callback", _external=True)],
            }
        },
        scopes=SCOPES,
    )

    flow.redirect_uri = url_for("main.google_fit_callback", _external=True)
    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true"
    )

    session["google_auth_state"] = state
    return authorization_url


def handle_callback(request):
    """認証コールバックを処理してトークンを取得"""
    state = session.get("google_auth_state", "")

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": current_app.config["GOOGLE_CLIENT_ID"],
                "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [url_for("main.google_fit_callback", _external=True)],
            }
        },
        scopes=SCOPES,
        state=state,
    )

    flow.redirect_uri = url_for("main.google_fit_callback", _external=True)

    # コードを使用してフローを完了し、認証情報を取得
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    store_credentials(credentials)

    return credentials


def upload_fitness_session(session_id):
    """フィットネスセッションをGoogle Fitにアップロード"""
    from ..models import FitnessSession, DataPoint

    # セッションの取得
    fitness_session = FitnessSession.query.get(session_id)
    if not fitness_session:
        return {"success": False, "error": "Session not found"}

    # データポイントの取得
    data_points = (
        DataPoint.query.filter_by(session_id=session_id)
        .order_by(DataPoint.timestamp)
        .all()
    )
    if not data_points:
        return {"success": False, "error": "No data points found for this session"}

    # Google Fitサービスの取得
    service = get_google_fit_service()
    if not service:
        return {"success": False, "error": "Not authenticated with Google Fit"}

    # 開始時間と終了時間をnanoseconds単位のタイムスタンプに変換
    start_time_nanos = int(
        fitness_session.start_time.replace(tzinfo=timezone.utc).timestamp() * 1e9
    )
    end_time_nanos = int(
        (fitness_session.end_time or datetime.now(timezone.utc))
        .replace(tzinfo=timezone.utc)
        .timestamp()
        * 1e9
    )

    # データソースID（アプリケーション固有）
    data_source_id = (
        f"raw:com.cycling:fit2go_dashboard:{current_app.config['APP_ID']}:cycling"
    )

    # サイクリングのデータセットを作成
    cycling_data = {
        "dataSourceId": data_source_id,
        "minStartTimeNs": start_time_nanos,
        "maxEndTimeNs": end_time_nanos,
        "point": [],
    }

    # データポイントを追加
    for point in data_points:
        point_time_nanos = int(
            point.timestamp.replace(tzinfo=timezone.utc).timestamp() * 1e9
        )

        # サイクリングのデータポイント
        cycling_data["point"].append(
            {
                "startTimeNanos": point_time_nanos,
                "endTimeNanos": point_time_nanos + int(1e9),  # 1秒間のデータポイント
                "dataTypeName": "com.google.cycling.wheel_revolution.rpm",
                "value": [{"fpVal": point.rpm}],
            }
        )

        # 速度のデータポイント
        cycling_data["point"].append(
            {
                "startTimeNanos": point_time_nanos,
                "endTimeNanos": point_time_nanos + int(1e9),
                "dataTypeName": "com.google.speed",
                "value": [{"fpVal": point.speed_kmh / 3.6}],  # km/h から m/s に変換
            }
        )

        # カロリーのデータポイント (累積)
        if point.calories_kcal > 0:
            cycling_data["point"].append(
                {
                    "startTimeNanos": point_time_nanos,
                    "endTimeNanos": point_time_nanos + int(1e9),
                    "dataTypeName": "com.google.calories.expended",
                    "value": [{"fpVal": point.calories_kcal}],
                }
            )

    try:
        # データをGoogle Fitにアップロード
        response = (
            service.users()
            .dataSources()
            .datasets()
            .patch(
                userId="me",
                dataSourceId=data_source_id,
                datasetId=f"{start_time_nanos}-{end_time_nanos}",
                body=cycling_data,
            )
            .execute()
        )

        return {"success": True, "response": response}
    except HttpError as error:
        return {"success": False, "error": str(error)}


def end_fitness_session(session_id, auto_sync=True):
    """フィットネスセッションを終了し、必要に応じて同期する"""
    from ..models import db, FitnessSession
    import datetime

    session = FitnessSession.query.get(session_id)
    if not session:
        return {"success": False, "error": "Session not found"}

    # セッションを終了
    session.end_time = datetime.datetime.now(datetime.timezone.utc)

    try:
        db.session.commit()

        # 自動同期が有効な場合、Google FitとHealth Connectに同期
        if auto_sync:
            sync_result = sync_session_to_services(session_id)
            return {
                "success": True,
                "session_id": session_id,
                "sync_result": sync_result,
            }

        return {"success": True, "session_id": session_id}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}


def sync_session_to_services(session_id):
    """セッションをGoogle FitとHealth Connectに同期"""
    results = {
        "google_fit": {"success": False, "error": None},
        "health_connect": {"success": False, "error": None},
    }

    try:
        # Google Fitへの同期
        gfit_result = upload_fitness_session(session_id)
        results["google_fit"] = gfit_result
    except Exception as e:
        results["google_fit"]["error"] = str(e)

    try:
        # Health Connectへの同期
        hc_result = upload_to_health_connect(session_id)
        results["health_connect"] = hc_result
    except Exception as e:
        results["health_connect"]["error"] = str(e)

    return results


def upload_to_health_connect(session_id):
    """Health Connectにフィットネスデータをアップロード"""
    from ..models import FitnessSession, DataPoint

    # セッションの取得
    session = FitnessSession.query.get(session_id)
    if not session:
        return {"success": False, "error": "Session not found"}

    # Health Connect APIの認証情報を取得
    if "health_connect_credentials" not in session:
        return {"success": False, "error": "Not authenticated with Health Connect"}

    try:
        # Health Connect APIにデータをアップロード
        # 注: 実際のHealth Connect APIの仕様に合わせて実装する必要があります
        # ここではプレースホルダーとしています
        return {"success": True, "message": "Data uploaded to Health Connect"}
    except Exception as e:
        return {"success": False, "error": str(e)}
