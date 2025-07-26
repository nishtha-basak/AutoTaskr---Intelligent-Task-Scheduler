from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os

class GoogleCalendarSync:
    def __init__(self):
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    def sync_schedule(self, schedule: list):
        """Sync generated schedule to Google Calendar"""
        # In real app, get user's credentials from DB
        creds = Credentials.from_authorized_user_info({
            'token': os.getenv('GOOGLE_ACCESS_TOKEN'),
            'refresh_token': os.getenv('GOOGLE_REFRESH_TOKEN'),
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scopes': ['https://www.googleapis.com/auth/calendar']
        })
        
        try:
            service = build('calendar', 'v3', credentials=creds)
            
            # Clear existing AutoTaskr events
            self._clear_existing_events(service)
            
            # Create new events
            for item in schedule:
                event = {
                    'summary': item['task'].title,
                    'description': item['task'].description,
                    'start': {'dateTime': item['start_time'].isoformat()},
                    'end': {'dateTime': item['end_time'].isoformat()},
                    'reminders': {'useDefault': True}
                }
                service.events().insert(
                    calendarId='primary',
                    body=event
                ).execute()
                
        except HttpError as error:
            print(f"Calendar sync failed: {error}")
    
    def _clear_existing_events(self, service):
        """Remove existing AutoTaskr events from calendar"""
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(
            calendarId='primary',
            q='AutoTaskr',
            timeMin=now,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        for event in events:
            if event['summary'].startswith('[AutoTaskr]'):
                service.events().delete(
                    calendarId='primary',
                    eventId=event['id']
                ).execute()