from datetime import datetime, timedelta
import heapq
import socket
import json
import logging
from models import Task
from log_config import *

class SchedulingEngine:
    def calculate_priority(self, task: Task) -> float:
        return (task.urgency * 0.6) + (task.importance * 0.4)

    def generate_schedule(self, tasks: list, start_time: datetime) -> list:
        if not tasks:
            return []

        queue = []
        for task in tasks:
            priority = self.calculate_priority(task)
            heapq.heappush(queue, (-priority, id(task), task))

        current_time = start_time
        schedule = []
        completed_ids = set()

        while queue:
            _, _, task = heapq.heappop(queue)

            if task.dependencies:
                deps = [int(d) for d in task.dependencies.split(',') if d]
                if not all(dep in completed_ids for dep in deps):
                    heapq.heappush(queue, (-self.calculate_priority(task), id(task), task))
                    continue

            end_time = current_time + timedelta(hours=task.duration)
            schedule.append({
                'task_id': task.id,
                'start_time': current_time,
                'end_time': end_time
            })
            completed_ids.add(task.id)
            self.dispatch_to_worker(task)
            current_time = end_time

        return schedule

    def dispatch_to_worker(self, task: Task):
        try:
            print(">>> Connecting to worker")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', 6000))
                s.sendall(json.dumps({
                    'task_id': task.id,
                    'title': task.title,
                    'duration': task.duration
                }).encode())
                s.settimeout(10)
                result = s.recv(1024)
                logging.info(f"[Master] Worker response: {result.decode()}")
        except Exception as e:
            logging.error(f"[Master] Worker error: {e}")
            print(f">>> WORKER CONNECTION FAILED: {e}")
    def generate_order(self, tasks: list) -> list:
        """Return task IDs in priority order (no timing)."""
        scored = sorted(
            tasks,
            key=lambda t: (t.urgency * 0.6 + t.importance * 0.4),
            reverse=True
        )
        return [task.id for task in scored]
