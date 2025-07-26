from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Task(db.Model):
    """Task model representing user tasks"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Float, nullable=False)  # Hours
    importance = db.Column(db.Integer, default=3)  # 1-5 scale
    urgency = db.Column(db.Integer, default=3)     # 1-5 scale
    dependencies = db.Column(db.String(200))       # Comma-separated task IDs
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    
    # Relationship to schedules
    schedules = db.relationship('Schedule', backref='task', lazy=True)
    
    def __repr__(self):
        return f'<Task {self.title}>'

class Schedule(db.Model):
    """Generated schedule model"""
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdjustmentLog(db.Model):
    """Log for schedule adjustments"""
    __tablename__ = 'adjustment_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    original_schedule_id = db.Column(db.Integer)
    new_schedule_id = db.Column(db.Integer)
    reason = db.Column(db.String(50))  # 'skipped', 'delayed', 'rescheduled'
    time_lost = db.Column(db.Float)    # Hours
    created_at = db.Column(db.DateTime, default=datetime.utcnow)