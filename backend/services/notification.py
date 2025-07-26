import smtplib
from email.message import EmailMessage

class Notifier:
    def send_notification(self, title: str, message: str):
        """Basic email notification without calendar integration"""
        msg = EmailMessage()
        msg.set_content(message)
        msg['Subject'] = f'AutoTaskr: {title}'
        msg['From'] = 'autotaskr@example.com'
        msg['To'] = 'user@example.com'
        
        try:
            with smtplib.SMTP('localhost', 1025) as server:  # Using test SMTP
                server.send_message(msg)
        except Exception as e:
            print(f"Notification failed: {e}")