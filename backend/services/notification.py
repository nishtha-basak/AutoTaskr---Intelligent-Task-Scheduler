import logging
from log_config import *

class Notifier:
    def send_notification(self, title: str, message: str):
        print(">>> Notifier called!")
        logging.info(f"[Notification] {title}: {message}")
        print(f"[Notification] {title} -> {message}")

