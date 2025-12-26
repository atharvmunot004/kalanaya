import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.actions import get_calendar_service, create_event, list_events, update_event, delete_event

service = get_calendar_service()

# 1) Create
created = create_event(
    service,
    title="Actions Layer Test",
    start_time="2025-12-20T18:00:00+05:30",
    end_time="2025-12-20T18:30:00+05:30",
    description="Testing calendar_actions.py",
)
print("CREATE:", created)

if created["status"] != "success":
    raise SystemExit("Create failed, stopping.")

event_id = created["event_id"]

# 2) List upcoming
listed = list_events(service, max_results=5)
print("LIST:", listed)

# 3) Update title
patched = update_event(service, event_id, {"summary": "Actions Layer Test (Updated)"})
print("UPDATE:", patched)

# 4) Delete (optional — comment out if you want to keep it)
deleted = delete_event(service, event_id)
print("DELETE:", deleted)
