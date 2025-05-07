from flask import Blueprint, request, jsonify, current_app
from ..models import db, FitnessSession, DataPoint
from datetime import datetime
import json

bp = Blueprint('api', __name__)

@bp.before_request
def verify_token():
    """APIトークンの検証"""
    token = request.headers.get('X-API-Token')
    if not token or token != current_app.config['API_TOKEN']:
        return jsonify({'error': 'Invalid API token'}), 401

@bp.route('/data', methods=['POST'])
def receive_data():
    """M5Stackからのデータ受信"""
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()
    device_id = data.get('device_id')
    if not device_id:
        return jsonify({'error': 'device_id is required'}), 400

    # アクティブなセッションを取得または新規作成
    session = FitnessSession.query.filter_by(
        device_id=device_id,
        end_time=None
    ).first()

    if not session:
        session = FitnessSession(
            device_id=device_id,
            start_time=datetime.utcnow()
        )
        db.session.add(session)

    # データポイントの作成
    data_point = DataPoint(
        session_id=session.id,
        timestamp=datetime.utcnow(),
        speed_kmh=data.get('speed_kmh', 0.0),
        rpm=data.get('rpm', 0.0),
        distance_km=data.get('distance_km', 0.0),
        calories_kcal=data.get('calories_kcal', 0.0),
        time_seconds=data.get('time_seconds', 0),
        mets=data.get('mets', 0.0)
    )
    db.session.add(data_point)

    # セッションデータの更新
    session.total_time_seconds = data.get('total_time_seconds', 0)
    session.total_distance_km = data.get('total_distance_km', 0.0)
    session.total_calories_kcal = data.get('total_calories_kcal', 0.0)
    session.average_speed_kmh = data.get('average_speed_kmh', 0.0)
    session.average_rpm = data.get('average_rpm', 0.0)
    session.average_mets = data.get('average_mets', 0.0)
    session.raw_data = data

    try:
        db.session.commit()
        return jsonify({'status': 'success', 'session_id': session.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/upload', methods=['POST'])
def upload_data():
    """SDカードのデータをアップロード"""
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()
    device_id = data.get('device_id')
    sessions = data.get('sessions', [])

    if not device_id or not sessions:
        return jsonify({'error': 'device_id and sessions are required'}), 400

    results = []
    for session_data in sessions:
        try:
            # セッションの作成または更新
            session = FitnessSession(
                device_id=device_id,
                start_time=datetime.fromisoformat(session_data.get('start_time')),
                end_time=datetime.fromisoformat(session_data.get('end_time')),
                total_time_seconds=session_data.get('total_time_seconds', 0),
                total_distance_km=session_data.get('total_distance_km', 0.0),
                total_calories_kcal=session_data.get('total_calories_kcal', 0.0),
                average_speed_kmh=session_data.get('average_speed_kmh', 0.0),
                average_rpm=session_data.get('average_rpm', 0.0),
                average_mets=session_data.get('average_mets', 0.0),
                raw_data=session_data
            )
            db.session.add(session)
            db.session.flush()  # セッションIDを取得するためにフラッシュ

            # データポイントの作成
            for point_data in session_data.get('data_points', []):
                data_point = DataPoint(
                    session_id=session.id,
                    timestamp=datetime.fromisoformat(point_data.get('timestamp')),
                    speed_kmh=point_data.get('speed_kmh', 0.0),
                    rpm=point_data.get('rpm', 0.0),
                    distance_km=point_data.get('distance_km', 0.0),
                    calories_kcal=point_data.get('calories_kcal', 0.0),
                    time_seconds=point_data.get('time_seconds', 0),
                    mets=point_data.get('mets', 0.0)
                )
                db.session.add(data_point)

            results.append({
                'status': 'success',
                'session_id': session.id,
                'start_time': session.start_time.isoformat()
            })
        except Exception as e:
            results.append({
                'status': 'error',
                'error': str(e),
                'start_time': session_data.get('start_time')
            })

    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'results': results
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500