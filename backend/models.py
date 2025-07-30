# models.py (updated for manual start, actual timings, and task status)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Float, nullable=False)
    urgency = db.Column(db.Integer, nullable=False)
    importance = db.Column(db.Integer, nullable=False)
    dependencies = db.Column(db.String(100), default="")
    completed = db.Column(db.Boolean, default=False)

    schedules = db.relationship("Schedule", backref="task", lazy=True)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)

    # Suggested order placement
    order = db.Column(db.Integer, nullable=False)

    # Actual execution fields
    start_actual = db.Column(db.DateTime, nullable=True)
    end_actual = db.Column(db.DateTime, nullable=True)

    # Status = 'pending' (default), 'in_progress', 'done', 'missed'
    status = db.Column(db.String(20), default="pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)  # Legacy field

class AdjustmentLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_schedule_id = db.Column(db.Integer)
    new_schedule_id = db.Column(db.Integer)
    reason = db.Column(db.String(100))
    time_lost = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
