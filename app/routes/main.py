from flask import Blueprint, render_template, jsonify, request
from ..models import db, FitnessSession, DataPoint
from datetime import datetime, timedelta
from sqlalchemy import func
import pytz
import json

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """ダッシュボードのメインページを表示"""
    return render_template('index.html')

@bp.route('/calendar')
def calendar():
    """カレンダービューを表示"""
    return render_template('calendar.html')

@bp.route('/api/sessions/current')
def get_current_session():
    """現在進行中のセッションデータを取得"""
    session = FitnessSession.query.filter_by(end_time=None).first()
    if not session:
        return jsonify({'status': 'no_active_session'})

    # 最新のデータポイントを取得
    latest_point = DataPoint.query.filter_by(session_id=session.id)\
        .order_by(DataPoint.timestamp.desc()).first()

    return jsonify({
        'session_id': session.id,
        'start_time': session.start_time.isoformat(),
        'total_time_seconds': session.total_time_seconds,
        'total_distance_km': session.total_distance_km,
        'total_calories_kcal': session.total_calories_kcal,
        'current_speed_kmh': latest_point.speed_kmh if latest_point else 0,
        'current_rpm': latest_point.rpm if latest_point else 0,
        'current_mets': latest_point.mets if latest_point else 0
    })

@bp.route('/api/sessions/daily')
def get_daily_stats():
    """指定された日の統計データを取得"""
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # 指定された日の期間を設定
    start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=1)

    # 15分単位でデータを集計
    interval = 15  # minutes
    stats = db.session.query(
        func.date_trunc('hour', DataPoint.timestamp) +
        func.floor(func.date_part('minute', DataPoint.timestamp) / interval) * 
        timedelta(minutes=interval),
        func.avg(DataPoint.speed_kmh).label('avg_speed'),
        func.avg(DataPoint.rpm).label('avg_rpm'),
        func.sum(DataPoint.distance_km).label('total_distance'),
        func.sum(DataPoint.calories_kcal).label('total_calories'),
        func.count(DataPoint.id).label('point_count')
    ).filter(
        DataPoint.timestamp.between(start_time, end_time)
    ).group_by(1).order_by(1).all()

    return jsonify([{
        'time': time.isoformat(),
        'avg_speed': float(avg_speed) if avg_speed else 0,
        'avg_rpm': float(avg_rpm) if avg_rpm else 0,
        'total_distance': float(total_distance) if total_distance else 0,
        'total_calories': float(total_calories) if total_calories else 0,
        'point_count': point_count
    } for time, avg_speed, avg_rpm, total_distance, total_calories, point_count in stats])

@bp.route('/api/sessions/cumulative')
def get_cumulative_stats():
    """累積統計データを取得"""
    stats = db.session.query(
        func.sum(FitnessSession.total_time_seconds).label('total_time'),
        func.sum(FitnessSession.total_distance_km).label('total_distance'),
        func.sum(FitnessSession.total_calories_kcal).label('total_calories')
    ).first()

    return jsonify({
        'total_time_seconds': int(stats.total_time) if stats.total_time else 0,
        'total_distance_km': float(stats.total_distance) if stats.total_distance else 0,
        'total_calories_kcal': float(stats.total_calories) if stats.total_calories else 0
    })