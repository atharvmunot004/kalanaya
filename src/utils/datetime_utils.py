"""DateTime utility functions."""

from datetime import datetime, timedelta, timezone
from typing import Optional

# Try to use zoneinfo (Python 3.9+), fallback to UTC offset for Windows compatibility
try:
    from zoneinfo import ZoneInfo
    DEFAULT_TZ = ZoneInfo("Asia/Kolkata")
except (ImportError, ModuleNotFoundError, LookupError):
    # Fallback: Asia/Kolkata is UTC+5:30
    DEFAULT_TZ = timezone(timedelta(hours=5, minutes=30))


def get_current_datetime(tz=None) -> datetime:
    """Get current datetime in the specified timezone (default: Asia/Kolkata)."""
    if tz is None:
        tz = DEFAULT_TZ
    return datetime.now(tz)


def parse_rfc3339(dt: str) -> datetime:
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


def to_rfc3339(dt: datetime) -> str:
    """Convert datetime to RFC3339 string."""
    return dt.isoformat()


def now_utc() -> str:
    """Get current UTC time as RFC3339 string."""
    return datetime.now(timezone.utc).isoformat()

