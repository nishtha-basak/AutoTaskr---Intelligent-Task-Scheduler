from flask import Flask, jsonify, request
from models import db, Task, Schedule
from scheduler import SchedulingEngine
from services.replanner import Reoptimizer
from services.notification import Notifier
from datetime import datetime, timedelta
import threading
import time
import atexit
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///autotaskr.db'
db.init_app(app)

# Initialize flag
scheduler_thread_started = False

def start_scheduler_thread():
    global scheduler_thread_started
    if not scheduler_thread_started:
        scheduler_thread = threading.Thread(target=background_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        scheduler_thread_started = True

def background_scheduler():
    with app.app_context():
        while True:
            delayed_tasks = Schedule.query.filter(
                Schedule.start_time < datetime.now(),
                Schedule.completed == False
            ).all()
            
            for task in delayed_tasks:
                Reoptimizer().reoptimize(task.id)
            time.sleep(300)  # Check every 5 minutes

# New initialization approach
with app.app_context():
    db.create_all()
    start_scheduler_thread()

# Register cleanup
atexit.register(lambda: print("Shutting down scheduler..."))

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.json
    new_task = Task(
        title=data['title'],
        duration=data['duration'],
        importance=data.get('importance', 3),
        urgency=data.get('urgency', 3),
        dependencies=','.join(map(str, data.get('dependencies', [])))
    )
    db.session.add(new_task)
    db.session.commit()
    optimize_schedule()
    return jsonify({"id": new_task.id}), 201

def optimize_schedule():
    tasks = Task.query.filter_by(completed=False).all()
    start_time = datetime.now().replace(hour=9, minute=0)
    schedule = SchedulingEngine().generate_schedule(tasks, start_time)
    
    Schedule.query.delete()
    for item in schedule:
        db.session.add(Schedule(
            task_id=item['task_id'],
            start_time=item['start_time'],
            end_time=item['end_time']
        ))
    db.session.commit()
    
    Notifier().send_notification(
        "New Schedule Generated",
        "Your optimized daily schedule is ready!"
    )

@app.route('/schedule', methods=['GET'])
def get_schedule():
    """Endpoint to fetch the current schedule"""
    today = datetime.now().date()
    schedules = Schedule.query.filter(
        Schedule.start_time >= today,
        Schedule.start_time < today + timedelta(days=1)
    ).order_by(Schedule.start_time).all()
    
    return jsonify([{
        'id': s.id,
        'title': s.task.title,
        'duration': s.task.duration,
        'start_time': s.start_time.isoformat(),
        'end_time': s.end_time.isoformat(),
        'urgency': s.task.urgency,
        'importance': s.task.importance
    } for s in schedules])

if __name__ == '__main__':
    app.run(debug=True)