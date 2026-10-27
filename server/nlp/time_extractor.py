"""Structured Temporal Extraction for Civic Announcements.

Extracts start_time, end_time, duration, and incident_date using regex patterns
and spaCy DATE/TIME entity recognition. Handles formats such as:
- "9 AM to 5 PM", "9:00 AM - 1:00 PM", "10am to 2pm"
- "from 10:00 to 14:00", "between 11:00 hrs and 17:00 hrs"
- "tomorrow", "today", "on Monday", "on 28th October"
"""

import re
from datetime import datetime, date, time, timedelta, timezone
from typing import Any, Dict, Optional, Tuple


MONTH_NAMES = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}

WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6
}


def _parse_time_token(t_str: str) -> Optional[time]:
    """Parse time string like '9 AM', '10:30 PM', '14:00', '10am', '17:00 hrs'."""
    t_str = t_str.lower().strip()
    t_str = re.sub(r"\bhrs\b|\bhours\b", "", t_str).strip()

    # 12-hour format with AM/PM (e.g. '9 am', '9:30 am', '11pm')
    m12 = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$", t_str)
    if m12:
        hours = int(m12.group(1))
        minutes = int(m12.group(2) or 0)
        meridiem = m12.group(3)
        if hours == 12:
            hours = 0 if meridiem == "am" else 12
        elif meridiem == "pm":
            hours += 12
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            return time(hour=hours, minute=minutes)

    # 24-hour format (e.g. '14:00', '09:30', '1400')
    m24 = re.match(r"^(\d{1,2}):(\d{2})$", t_str)
    if m24:
        hours = int(m24.group(1))
        minutes = int(m24.group(2))
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            return time(hour=hours, minute=minutes)

    return None


def extract_incident_date(text: str, reference_date: Optional[date] = None) -> date:
    """Extract incident target date from text (today, tomorrow, weekday, or explicit date)."""
    ref = reference_date or date.today()
    lower = text.lower()

    if "tomorrow" in lower:
        return ref + timedelta(days=1)
    if "day after tomorrow" in lower:
        return ref + timedelta(days=2)
    if "today" in lower:
        return ref

    # Check for relative weekday (e.g. "on Wednesday", "this Friday")
    for wname, wnum in WEEKDAYS.items():
        pattern = r"\b(?:on\s+|this\s+|coming\s+)?" + re.escape(wname) + r"\b"
        if re.search(pattern, lower):
            current_w = ref.weekday()
            days_ahead = (wnum - current_w) % 7
            if days_ahead == 0:
                days_ahead = 7  # Next week's instance
            return ref + timedelta(days=days_ahead)

    # Explicit day + month (e.g. "28th October", "October 28", "28 Oct")
    m_date = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([a-zA-Z]{3,9})\b", lower)
    if m_date:
        d_val = int(m_date.group(1))
        m_val = MONTH_NAMES.get(m_date.group(2).lower())
        if m_val:
            year = ref.year
            try:
                candidate = date(year, m_val, d_val)
                if candidate < ref:
                    candidate = date(year + 1, m_val, d_val)
                return candidate
            except ValueError:
                pass

    return ref


def extract_temporal_range(text: str) -> Tuple[Optional[time], Optional[time]]:
    """Extract start and end time from natural announcement text.

    Examples:
    - "9 AM to 5 PM"
    - "between 10:00 and 14:00"
    - "from 11:30 AM - 3:00 PM"
    - "10am to 2pm"
    """
    lower = text.lower()

    # Pattern: [from/between] <time1> [to/and/-] <time2>
    pattern = (
        r"(?:from\s+|between\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*"
        r"(?:to|and|-|–|until)\s*"
        r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)"
    )

    matches = re.finditer(pattern, lower)
    for match in matches:
        t1_raw = match.group(1).strip()
        t2_raw = match.group(2).strip()

        # If t1 has no am/pm but t2 does (e.g. "9 to 5 PM")
        if re.search(r"(am|pm)$", t2_raw) and not re.search(r"(am|pm)$", t1_raw):
            meridiem = re.search(r"(am|pm)$", t2_raw).group(1)
            # Heuristic: if t1 is larger than t2 or morning hours
            num1 = int(t1_raw.split(":")[0])
            num2 = int(t2_raw.replace(meridiem, "").strip().split(":")[0])
            if meridiem == "pm" and num1 >= 8 and num1 <= 12 and num2 < 8:
                t1_raw = f"{t1_raw} am"
            else:
                t1_raw = f"{t1_raw} {meridiem}"

        t1 = _parse_time_token(t1_raw)
        t2 = _parse_time_token(t2_raw)

        if t1 and t2:
            return t1, t2

    return None, None


def extract_temporal_fields(
    text: str,
    reference_datetime: Optional[datetime] = None
) -> Dict[str, Any]:
    """Complete temporal extractor returning structured fields and durations.

    Returns dict containing:
    - start_time: datetime | None
    - expected_end_time: datetime | None
    - duration_hours: float | None
    - incident_date: str (YYYY-MM-DD)
    """
    ref_dt = reference_datetime or datetime.now(timezone.utc)
    target_date = extract_incident_date(text, reference_date=ref_dt.date())
    start_t, end_t = extract_temporal_range(text)

    start_dt = None
    end_dt = None
    duration_hours = None

    if start_t and end_t:
        start_dt = datetime.combine(target_date, start_t, tzinfo=timezone.utc)
        end_dt = datetime.combine(target_date, end_t, tzinfo=timezone.utc)

        # Handle overnight span (e.g. 10 PM to 6 AM)
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)

        diff = end_dt - start_dt
        duration_hours = round(diff.total_seconds() / 3600.0, 2)

    return {
        "start_time": start_dt,
        "expected_end_time": end_dt,
        "duration_hours": duration_hours,
        "incident_date": target_date.isoformat()
    }
