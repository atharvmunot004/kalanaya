import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.actions import get_calendar_service

service = get_calendar_service()

event = {
    'summary': 'API Test Event',
    'description': 'If you see this, the API works.',
    'start': {
        'dateTime': '2025-12-20T15:00:00',
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': '2025-12-20T16:00:00',
        'timeZone': 'Asia/Kolkata',
    },
}

created_event = service.events().insert(
    calendarId='primary',
    body=event
).execute()

print("Event created:")
print(created_event.get('htmlLink'))
