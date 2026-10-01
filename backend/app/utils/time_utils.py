from datetime import datetime, timezone, time, date
from typing import Optional

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def parse_time_str(time_str: str) -> time:
    """Parses 'HH:MM' or 'HH:MM:SS' string into a time object."""
    parts = [int(p) for p in time_str.split(":")]
    if len(parts) == 2:
        return time(hour=parts[0], minute=parts[1])
    elif len(parts) == 3:
        return time(hour=parts[0], minute=parts[1], second=parts[2])
    raise ValueError(f"Invalid time string: {time_str}")

def format_time_str(t: time) -> str:
    return t.strftime("%H:%M")

def time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute

def minutes_to_time(minutes: int) -> time:
    minutes = minutes % (24 * 60)
    hour = minutes // 60
    minute = minutes % 60
    return time(hour=hour, minute=minute)

def format_duration(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{mins}m"
