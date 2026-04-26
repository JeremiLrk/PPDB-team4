from datetime import date, datetime, time, timedelta, timezone

from server.app.models.availability_block import AvailabilityBlock
from server.extensions import db

UTC_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
WEEKDAY_LABELS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

def parse_weekday(value):
    if value is None or isinstance(value, bool):
        return None

    try:
        weekday = int(value)
    except (TypeError, ValueError):
        return None

    if weekday < 0 or weekday > 6:
        return None
    return weekday

def parse_time_value(value):
    if not isinstance(value, str):
        return None
    try:
        return time.fromisoformat(value.strip())
    except ValueError:
        return None

def weekday_label(weekday):
    if weekday is None or weekday < 0 or weekday > 6:
        return "Unknown"
    return WEEKDAY_LABELS[weekday]

def occurrence_date_for_weekday(weekday, reference_date: date | None = None):
    current_date = reference_date or datetime.utcnow().date()
    days_ahead = (weekday - current_date.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return current_date + timedelta(days=days_ahead)

def recurrence_for_block(block):
    if block.weekday is not None and block.start_time is not None and block.end_time is not None:
        return block.weekday, block.start_time, block.end_time
    if block.start_at is not None and block.end_at is not None:
        return block.start_at.weekday(), block.start_at.time(), block.end_at.time()

    return None

def weekly_window_for_block(block, week_start_date: date):
    recurrence = recurrence_for_block(block)
    if recurrence is None:
        return None

    weekday, start_time_value, end_time_value = recurrence
    target_date = week_start_date + timedelta(days=weekday)
    return datetime.combine(target_date, start_time_value), datetime.combine(target_date, end_time_value)

def legacy_datetimes_for_weekday(weekday, start_time_value, end_time_value):
    target_date = occurrence_date_for_weekday(weekday)
    return datetime.combine(target_date, start_time_value), datetime.combine(target_date, end_time_value)

def parse_timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        normalized_value = value.strip()
        if normalized_value.endswith("Z"):
            normalized_value = normalized_value[:-1] + "+00:00"

        parsed = datetime.fromisoformat(normalized_value)
        if parsed.tzinfo is None:
            return None

        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    except ValueError:
        return None

def serialize_block(block):
    recurrence = recurrence_for_block(block)
    weekday = recurrence[0] if recurrence else None
    start_time_value = recurrence[1] if recurrence else None
    end_time_value = recurrence[2] if recurrence else None
    start_utc = block.start_at.replace(tzinfo=timezone.utc)
    end_utc = block.end_at.replace(tzinfo=timezone.utc)
    return {
        "id": block.id,
        "weekday": weekday,
        "weekday_label": weekday_label(weekday),
        "start_time": start_time_value.isoformat(timespec="minutes") if start_time_value else None,
        "end_time": end_time_value.isoformat(timespec="minutes") if end_time_value else None,
        "start_at": start_utc.strftime(UTC_TIMESTAMP_FORMAT),
        "end_at": end_utc.strftime(UTC_TIMESTAMP_FORMAT),
    }

def list_blocks_for_user(user_id):
    blocks = (
        AvailabilityBlock.query.filter_by(user_id=user_id)
        .order_by(AvailabilityBlock.weekday.asc(), AvailabilityBlock.start_time.asc(), AvailabilityBlock.id.asc())
        .all()
    )
    return [serialize_block(block) for block in blocks]

def has_overlap(user_id, weekday, start_time_value, end_time_value):
    for block in AvailabilityBlock.query.filter_by(user_id=user_id).all():
        existing_window = recurrence_for_block(block)
        if existing_window is None:
            continue

        if existing_window[0] != weekday:
            continue

        if existing_window[1] < end_time_value and existing_window[2] > start_time_value:
            return True

    return False

def create_block_for_user(user_id, weekday, start_time_value, end_time_value):
    start_at, end_at = legacy_datetimes_for_weekday(weekday, start_time_value, end_time_value)
    block = AvailabilityBlock(
        user_id=user_id,
        weekday=weekday,
        start_time=start_time_value,
        end_time=end_time_value,
        start_at=start_at,
        end_at=end_at,
    )
    db.session.add(block)
    db.session.commit()
    return serialize_block(block)


def delete_block_for_user(user_id, block_id):
    block = AvailabilityBlock.query.filter_by(id=block_id, user_id=user_id).first()
    if not block:
        return False
    db.session.delete(block)
    db.session.commit()
    return True
