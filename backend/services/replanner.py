from backend.models import Task, db, Schedule, AdjustmentLog
from backend.scheduler import SchedulingEngine
from datetime import datetime, timedelta
import threading

class Reoptimizer:
    def reoptimize(self, skipped_schedule_id: int):
        """Re-optimize schedule after task delay or skip"""
        skipped = Schedule.query.get(skipped_schedule_id)
        if not skipped:
            return
        
        # Calculate time lost
        time_lost = 0
        if skipped.start_time < datetime.now():
            time_lost = (datetime.now() - skipped.start_time).total_seconds() / 3600
        
        # Get all pending tasks (including skipped)
        pending_tasks = Task.query.filter(
            Task.completed == False
        ).all()
        
        # Get last completed task end time or current time
        last_completed = Schedule.query.filter(
            Schedule.completed == True
        ).order_by(Schedule.end_time.desc()).first()
        
        start_time = datetime.now()
        if last_completed and last_completed.end_time > start_time:
            start_time = last_completed.end_time
        
        # Generate new schedule
        engine = SchedulingEngine()
        new_schedule = engine.generate_schedule(pending_tasks, start_time)
        
        # Update database in a transaction
        with db.session.begin():
            # Clear existing schedules
            Schedule.query.filter(
                Schedule.completed == False
            ).delete()
            
            # Add new schedules
            for item in new_schedule:
                new_sched = Schedule(
                    task_id=item['task_id'],
                    start_time=item['start_time'],
                    end_time=item['end_time']
                )
                db.session.add(new_sched)
            
            # Log adjustment
            new_first_task = new_schedule[0]['task_id'] if new_schedule else None
            adjustment = AdjustmentLog(
                original_schedule_id=skipped_schedule_id,
                new_schedule_id=new_first_task,
                reason='skipped' if skipped.completed else 'delayed',
                time_lost=time_lost
            )
            db.session.add(adjustment)
        
        # Notify user in background thread
        threading.Thread(
            target=self._notify_replan,
            args=(skipped.task.title, time_lost)
        ).start()
    
    def _notify_replan(self, task_name: str, time_lost: float):
        """Notify user about schedule replanning"""
        from services.notification import Notifier
        
        if time_lost > 0:
            message = f"Schedule re-optimized! Lost {time_lost:.1f} hours due to delay with '{task_name}'."
        else:
            message = f"Schedule re-optimized after skipping '{task_name}'."
        
        Notifier().send_notification("Schedule Updated", message)