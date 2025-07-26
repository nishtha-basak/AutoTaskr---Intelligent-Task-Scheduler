from datetime import datetime, timedelta
import heapq
from backend.models import Task

class SchedulingEngine:
    def calculate_priority(self, task: Task) -> float:
        """Calculate task priority using weighted factors"""
        return (task.urgency * 0.6) + (task.importance * 0.4)

    def generate_schedule(self, tasks: list, start_time: datetime) -> list:
        """Generate optimized schedule using priority queue"""
        if not tasks:
            return []
        
        # Create priority queue (max-heap using negative priority)
        queue = []
        for task in tasks:
            priority = self.calculate_priority(task)
            heapq.heappush(queue, (-priority, id(task), task))
        
        current_time = start_time
        schedule = []
        completed_ids = set()
        
        while queue:
            _, _, task = heapq.heappop(queue)
            
            # Check dependencies
            if task.dependencies:
                deps = [int(d) for d in task.dependencies.split(',') if d]
                if not all(dep in completed_ids for dep in deps):
                    heapq.heappush(queue, (-self.calculate_priority(task), id(task), task))
                    continue
            
            # Schedule the task
            end_time = current_time + timedelta(hours=task.duration)
            schedule.append({
                'task_id': task.id,
                'start_time': current_time,
                'end_time': end_time
            })
            completed_ids.add(task.id)
            current_time = end_time
            
        return schedule