from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError





# ---------- Helpers ----------


def _parse_rfc3339(dt: str) -> datetime:
    """
    Parse RFC3339 datetime string into a timezone-aware datetime.
    Uses built-in datetime.fromisoformat() instead of dateutil.
    """
    # Handle 'Z' suffix (UTC) - replace with +00:00
    if dt.endswith('Z'):
        dt = dt[:-1] + '+00:00'
    # Handle format without timezone info - assume UTC
    elif '+' not in dt and (len(dt) < 6 or dt[-6] not in ['+', '-']):
        # Check if it ends with digits (no timezone), add UTC
        if dt[-1].isdigit():
            dt = dt + '+00:00'
    return datetime.fromisoformat(dt)


def _to_rfc3339(dt: datetime) -> str:
    """
    Convert datetime back to RFC3339 string.
    """
    return dt.isoformat()


def _ensure_rfc3339(dt: str) -> str:
    """
    Accepts an RFC3339-ish string. If user provides ISO8601 without timezone,
    Google may interpret it oddly. Strongly prefer timezone-aware strings.
    """
    # We keep it minimal for MVP: assume caller passes proper RFC3339.
    # Example: "2025-12-20T15:00:00+05:30"
    return dt


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_result(status: str, **kwargs) -> Dict[str, Any]:
    out = {"status": status}
    out.update(kwargs)
    return out


# ---------- Core Actions ----------

def create_event(
    service: Resource,
    title: str,
    start_time: str,
    end_time: Optional[str],
    *,
    description: str = "",
    location: str = "",
    attendees: Optional[List[str]] = None,
    calendar_id: str = "primary",
    timezone_str: str = "Asia/Kolkata",
    reminders: Optional[Dict[str, Any]] = None,
    all_day: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Create a calendar event.

    Safety guarantees:
    - start_time MUST exist
    - if end_time is None and all_day is False/None: default to start_time + 1 hour
    - if end_time is None and all_day is True: default to start_time + 1 day (date format)
    - timestamps are enforced as RFC3339 for timed events
    - dates are in YYYY-MM-DD format for all-day events
    
    Args:
        all_day: If True, creates an all-day event using 'date' field instead of 'dateTime'
    """

    attendees = attendees or []

    try:
        if all_day:
            # All-day event: use 'date' field (YYYY-MM-DD format)
            # start_time and end_time should be date strings
            start_date = start_time  # Should already be in YYYY-MM-DD format
            
            if end_time:
                end_date = end_time  # Should already be in YYYY-MM-DD format
            else:
                # Default: end date is start date + 1 day (exclusive)
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = start_dt + timedelta(days=1)
                end_date = end_dt.strftime("%Y-%m-%d")
            
            event_body: Dict[str, Any] = {
                "summary": title,
                "description": description,
                "location": location,
                "start": {
                    "date": start_date,
                },
                "end": {
                    "date": end_date,
                },
            }
        else:
            # Timed event: use 'dateTime' field
            start_dt = _parse_rfc3339(start_time)

            if end_time:
                end_dt = _parse_rfc3339(end_time)
            else:
                # HARD GUARANTEE: default duration = 1 hour
                end_dt = start_dt + timedelta(hours=1)

            event_body: Dict[str, Any] = {
                "summary": title,
                "description": description,
                "location": location,
                "start": {
                    "dateTime": _to_rfc3339(start_dt),
                    "timeZone": timezone_str,
                },
                "end": {
                    "dateTime": _to_rfc3339(end_dt),
                    "timeZone": timezone_str,
                },
            }

        if attendees:
            event_body["attendees"] = [
                {"email": a.strip()} for a in attendees if a.strip()
            ]

        if reminders:
            event_body["reminders"] = reminders

        created = (
            service.events()
            .insert(calendarId=calendar_id, body=event_body)
            .execute()
        )

        return _to_result(
            "success",
            action="create_event",
            event_id=created.get("id"),
            html_link=created.get("htmlLink"),
            summary=created.get("summary"),
            start=created.get("start"),
            end=created.get("end"),
        )

    except Exception as e:
        return _to_result(
            "error",
            action="create_event",
            error=str(e),
        )


def list_events(
    service: Resource,
    *,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    query: Optional[str] = None,
    max_results: int = 10,
    calendar_id: str = "primary",
    single_events: bool = True,
    order_by: str = "startTime",
) -> Dict[str, Any]:
    """
    List events in a window with robust time window defaults.
    
    Time window normalization (LE-01):
    - If both time_min and time_max are None: defaults to [now → now + 24 hours]
    - If time_min is provided but time_max is None: set time_max = time_min + 24 hours
    - If time_min is at 00:00:00, treat it as a full-day query starting at that date
    - All defaults computed inside this function
    
    Provide RFC3339 strings for time_min/time_max.
    """
    # Normalize time window defaults
    now_dt = datetime.now(timezone.utc)
    
    if time_min is None and time_max is None:
        # Both missing: default to [now → now + 24 hours]
        time_min_dt = now_dt
        time_max_dt = now_dt + timedelta(hours=24)
        time_min = _to_rfc3339(time_min_dt)
        time_max = _to_rfc3339(time_max_dt)
    elif time_min is not None and time_max is None:
        # Only time_min provided: set time_max = time_min + 24 hours
        time_min_dt = _parse_rfc3339(time_min)
        
        # Check if time_min is at 00:00:00 (full-day query indicator)
        if time_min_dt.hour == 0 and time_min_dt.minute == 0 and time_min_dt.second == 0:
            # Treat as full-day: end at 23:59:59 of the same day
            time_max_dt = time_min_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            # Normal case: add 24 hours
            time_max_dt = time_min_dt + timedelta(hours=24)
        
        time_max = _to_rfc3339(time_max_dt)
    elif time_min is None and time_max is not None:
        # Only time_max provided: set time_min = now
        time_min = _to_rfc3339(now_dt)
        # time_max already set, no change needed
    # else: both time_min and time_max provided, use as-is

    try:
        resp = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                q=query,
                maxResults=max_results,
                singleEvents=single_events,
                orderBy=order_by if single_events else None,
            )
            .execute()
        )
        items = resp.get("items", [])
        events = []
        for it in items:
            events.append(
                {
                    "id": it.get("id"),
                    "summary": it.get("summary"),
                    "start": it.get("start"),
                    "end": it.get("end"),
                    "location": it.get("location"),
                    "htmlLink": it.get("htmlLink"),
                    "status": it.get("status"),
                }
            )
        return _to_result("success", action="list_events", events=events, count=len(events))
    except HttpError as e:
        return _to_result("error", action="list_events", error=str(e))


def find_events(
    service: Resource,
    *,
    title_contains: str,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 10,
    calendar_id: str = "primary",
) -> Dict[str, Any]:
    """
    Convenience wrapper: search by title keyword (uses 'q' query).
    """
    return list_events(
        service,
        time_min=time_min,
        time_max=time_max,
        query=title_contains,
        max_results=max_results,
        calendar_id=calendar_id,
    )


def update_event(
    service: Resource,
    event_id: str,
    updates: Dict[str, Any],
    *,
    calendar_id: str = "primary",
) -> Dict[str, Any]:
    """
    Patch an event by event_id. `updates` is a partial event resource.
    Examples:
      {"summary": "New Title"}
      {"start": {"dateTime": "...", "timeZone": "Asia/Kolkata"}, "end": {...}}
    """
    try:
        updated = (
            service.events()
            .patch(calendarId=calendar_id, eventId=event_id, body=updates)
            .execute()
        )
        return _to_result(
            "success",
            action="update_event",
            event_id=updated.get("id"),
            html_link=updated.get("htmlLink"),
            summary=updated.get("summary"),
            start=updated.get("start"),
            end=updated.get("end"),
        )
    except HttpError as e:
        return _to_result("error", action="update_event", error=str(e), event_id=event_id)


def delete_event(
    service: Resource,
    event_id: str,
    *,
    calendar_id: str = "primary",
) -> Dict[str, Any]:
    """
    Delete an event by id.
    """
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return _to_result("success", action="delete_event", event_id=event_id)
    except HttpError as e:
        return _to_result("error", action="delete_event", error=str(e), event_id=event_id)
