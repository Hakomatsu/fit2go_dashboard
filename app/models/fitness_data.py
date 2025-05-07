from datetime import datetime

from . import db


class FitnessSession(db.Model):
    __tablename__ = "fitness_sessions"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    total_time_seconds = db.Column(db.Integer, default=0)
    total_distance_km = db.Column(db.Float, default=0.0)
    total_calories_kcal = db.Column(db.Float, default=0.0)
    average_speed_kmh = db.Column(db.Float, default=0.0)
    average_rpm = db.Column(db.Float, default=0.0)
    average_mets = db.Column(db.Float, default=0.0)
    raw_data = db.Column(db.JSON)  # SQLiteではJSON型を使用
    data_points = db.relationship(
        "DataPoint", backref="session", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<FitnessSession {self.id} - {self.start_time}>"


class DataPoint(db.Model):
    __tablename__ = "data_points"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey("fitness_sessions.id"), nullable=False
    )
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    speed_kmh = db.Column(db.Float)
    rpm = db.Column(db.Float)
    distance_km = db.Column(db.Float)
    calories_kcal = db.Column(db.Float)
    time_seconds = db.Column(db.Integer)
    mets = db.Column(db.Float)

    def __repr__(self):
        return f"<DataPoint {self.id} - {self.timestamp}>"
