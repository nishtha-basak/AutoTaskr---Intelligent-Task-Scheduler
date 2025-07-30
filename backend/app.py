from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import threading
import logging
import time
from log_config import *
from models import db, Task, Schedule
from scheduler import SchedulingEngine
from services.replanner import Reoptimizer

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)
CORS(app)

# ✅ Background checker

def background_scheduler():
    with app.app_context():
        while True:
            now = datetime.now()
            pending = Schedule.query.filter(Schedule.status == 'in_progress').all()
            for sched in pending:
                if sched.end_actual and now > sched.end_actual + timedelta(minutes=10):
                    sched.status = 'missed'

                    # ✅ Clone missed task
                    original = sched.task
                    new_task = Task(
                        title=f"{original.title} (Retry)",
                        duration=original.duration,
                        urgency=original.urgency,
                        importance=original.importance,
                        dependencies=original.dependencies
                    )
                    db.session.add(new_task)
                    db.session.commit()

                    logging.warning(f"[AutoMissed] Task '{original.title}' missed. Cloned as new task.")
                    Reoptimizer().reoptimize(sched.id)

                    db.session.commit()
            time.sleep(60)

@app.route("/tasks", methods=["POST"])
def add_task():
    data = request.get_json()
    task = Task(
        title=data["title"],
        duration=data["duration"],
        urgency=data["urgency"],
        importance=data["importance"]
    )
    db.session.add(task)
    db.session.commit()

    tasks = Task.query.filter(Task.completed == False).all()
    active_task_ids = [t.id for t in tasks]

    engine = SchedulingEngine()
    ordered = engine.generate_order(tasks)

    Schedule.query.filter(Schedule.task_id.in_(active_task_ids)).delete()
    db.session.commit()

    for i, task_id in enumerate(ordered):
        db.session.add(Schedule(task_id=task_id, order=i + 1))

    db.session.commit()
    return jsonify({"message": "Task added and schedule updated."}), 201

@app.route("/schedule", methods=["GET"])
def get_schedule():
    schedules = Schedule.query.order_by(Schedule.order).all()
    seen = set()
    result = []

    for sched in schedules:
        if sched.task_id in seen:
            continue
        seen.add(sched.task_id)

        result.append({
            "id": sched.id,
            "title": sched.task.title,
            "duration": sched.task.duration,
            "urgency": sched.task.urgency,
            "importance": sched.task.importance,
            "status": sched.status,
            "start_actual": sched.start_actual.isoformat() if sched.start_actual else None,
            "end_actual": sched.end_actual.isoformat() if sched.end_actual else None
        })

    return jsonify(result)

@app.route("/schedule/<int:sched_id>/start", methods=["PATCH"])
def start_task(sched_id):
    sched = db.session.get(Schedule, sched_id)
    if not sched:
        return jsonify({"error": "Task not found"}), 404

    now = datetime.now()
    sched.start_actual = now
    sched.end_actual = now + timedelta(hours=sched.task.duration)
    sched.status = "in_progress"
    db.session.commit()
    return jsonify({"message": "Task started", "end_time": sched.end_actual.isoformat()}), 200

@app.route("/schedule/<int:sched_id>/complete", methods=["PATCH"])
def complete_task(sched_id):
    sched = db.session.get(Schedule, sched_id)
    if not sched:
        return jsonify({"error": "Task not found"}), 404

    now = datetime.now()
    if sched.end_actual and now <= sched.end_actual + timedelta(minutes=10):
        sched.status = "done"
        sched.completed = True
        db.session.commit()
        return jsonify({"message": "Task marked as done"}), 200
    else:
        return jsonify({"error": "Too late to complete this task"}), 400

@app.route("/replan", methods=["POST"])
def manual_replan():
    now = datetime.now()
    overdue = Schedule.query.filter(Schedule.end_actual < now, Schedule.status == 'in_progress').first()
    if overdue:
        Reoptimizer().reoptimize(overdue.id)
    return jsonify({"status": "replan triggered"}), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        threading.Thread(target=background_scheduler, daemon=True).start()
    app.run(debug=True)
