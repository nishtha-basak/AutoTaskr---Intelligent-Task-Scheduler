# replanner.py (fixed nested transaction issue)
from models import Task, db, Schedule, AdjustmentLog
from scheduler import SchedulingEngine
from datetime import datetime
import threading
import logging
from log_config import *

class Reoptimizer:
    def reoptimize(self, skipped_schedule_id: int):
        skipped = Schedule.query.get(skipped_schedule_id)
        if not skipped:
            logging.warning(f"[Reoptimizer] Skipped schedule ID {skipped_schedule_id} not found.")
            return

        time_lost = 0
        if skipped.start_actual and skipped.start_actual < datetime.now():

            # was: time_lost = (datetime.now() - skipped.start_time).total_seconds() / 3600
            time_lost = (datetime.now() - skipped.start_actual).total_seconds() / 3600 if skipped.start_actual else 0

        pending_tasks = Task.query.filter(Task.completed == False).all()

        last_completed = Schedule.query.filter(
            Schedule.completed == True
        ).order_by(Schedule.end_time.desc()).first()

        start_time = max(datetime.now(), last_completed.end_time if last_completed else datetime.now())

        engine = SchedulingEngine()
        new_schedule = engine.generate_schedule(pending_tasks, start_time)

        Schedule.query.filter(Schedule.completed == False).delete()

        new_first_task = None
        for item in new_schedule:
            new_sched = Schedule(
                task_id=item['task_id'],
                start_time=item['start_time'],
                end_time=item['end_time']
            )
            db.session.add(new_sched)
            if new_first_task is None:
                new_first_task = new_sched

        adjustment = AdjustmentLog(
            original_schedule_id=skipped_schedule_id,
            new_schedule_id=new_first_task.id if new_first_task else None,
            reason='skipped' if skipped.completed else 'delayed',
            time_lost=time_lost
        )
        db.session.add(adjustment)
        db.session.commit()

        logging.info(f"[Reoptimizer] Schedule re-optimized. Time lost: {time_lost:.2f} hrs. Task: {skipped.task.title}")
        threading.Thread(
            target=self._notify_replan,
            args=(skipped.task.title, time_lost)
        ).start()

    def _notify_replan(self, task_name: str, time_lost: float):
        from services.notification import Notifier
        message = (
            f"Schedule re-optimized! Lost {time_lost:.1f} hours due to delay with '{task_name}'."
            if time_lost > 0 else
            f"Schedule re-optimized after skipping '{task_name}'."
        )
        logging.info(f"[Notification] {message}")
        Notifier().send_notification("Schedule Updated", message)