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
    """Parse a weekday value from a string or integer, returning an integer 0-6 or None if invalid."""
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
    """Parse a time value from a string in HH:MM format, returning a time object or None if invalid."""
    if not isinstance(value, str):
        return None
    try:
        return time.fromisoformat(value.strip())
    except ValueError:
        return None

def weekday_label(weekday):
    """Convert a weekday integer (0-6) to its corresponding label, or return 'Unknown' if invalid."""
    if weekday is None or weekday < 0 or weekday > 6:
        return "Unknown"
    return WEEKDAY_LABELS[weekday]

def occurrence_date_for_weekday(weekday, reference_date: date | None = None):
    """Calculate the next occurrence date for a given weekday (0=Monday, 6=Sunday) starting from reference_date or today."""
    current_date = reference_date or datetime.utcnow().date()
    days_ahead = (weekday - current_date.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return current_date + timedelta(days=days_ahead)

def recurrence_for_block(block):
    """Determine the recurrence pattern for an AvailabilityBlock, returning (weekday, start_time, end_time) or None if not recurring."""
    if block.weekday is not None and block.start_time is not None and block.end_time is not None:
        return block.weekday, block.start_time, block.end_time
    if block.start_at is not None and block.end_at is not None:
        return block.start_at.weekday(), block.start_at.time(), block.end_at.time()

    return None

def weekly_window_for_block(block, week_start_date: date):
    """Calculate the start and end datetimes for the given AvailabilityBlock within the week starting at week_start_date, or return None if the block does not have a valid recurrence pattern."""
    recurrence = recurrence_for_block(block)
    if recurrence is None:
        return None

    weekday, start_time_value, end_time_value = recurrence
    target_date = week_start_date + timedelta(days=weekday)
    return datetime.combine(target_date, start_time_value), datetime.combine(target_date, end_time_value)

def legacy_datetimes_for_weekday(weekday, start_time_value, end_time_value):
    """Calculate start_at and end_at datetimes for a given weekday and time values, using the next occurrence of that weekday as the date component."""
    target_date = occurrence_date_for_weekday(weekday)
    return datetime.combine(target_date, start_time_value), datetime.combine(target_date, end_time_value)

def parse_timestamp(value):
    """Parse a timestamp string in ISO 8601 format, returning a timezone-aware datetime in UTC or None if invalid."""
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
    """Convert an AvailabilityBlock instance to a dictionary representation, including recurrence information and UTC timestamps."""
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
    """List all availability blocks for a given user, ordered by weekday and start time."""
    blocks = (
        AvailabilityBlock.query.filter_by(user_id=user_id)
        .order_by(AvailabilityBlock.weekday.asc(), AvailabilityBlock.start_time.asc(), AvailabilityBlock.id.asc())
        .all()
    )
    return [serialize_block(block) for block in blocks]

def has_overlap(user_id, weekday, start_time_value, end_time_value):
    """Check if the given time window overlaps with any existing availability blocks for the user on the same weekday."""
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
    """Create a new availability block for the user with the given weekday and time values, ensuring there are no overlaps with existing blocks."""
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
    """Delete an availability block for the user by block ID, returning True if the block was found and deleted, or False if the block was not found."""
    block = AvailabilityBlock.query.filter_by(id=block_id, user_id=user_id).first()
    if not block:
        return False
    db.session.delete(block)
    db.session.commit()
    return True
