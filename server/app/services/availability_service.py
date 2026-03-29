from datetime import datetime, timezone

from sqlalchemy import and_

from server.app.models.availability_block import AvailabilityBlock
from server.extensions import db

UTC_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

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
    start_utc = block.start_at.replace(tzinfo=timezone.utc)
    end_utc = block.end_at.replace(tzinfo=timezone.utc)
    return {
        "id": block.id,
        "start_at": start_utc.strftime(UTC_TIMESTAMP_FORMAT),
        "end_at": end_utc.strftime(UTC_TIMESTAMP_FORMAT),
    }

def list_blocks_for_user(user_id):
    blocks = (
        AvailabilityBlock.query.filter_by(user_id=user_id)
        .order_by(AvailabilityBlock.start_at.asc(), AvailabilityBlock.id.asc())
        .all()
    )
    return [serialize_block(block) for block in blocks]

def has_overlap(user_id, start_at, end_at):
    return (
        AvailabilityBlock.query.filter(
            and_(
                AvailabilityBlock.user_id == user_id,
                AvailabilityBlock.start_at < end_at,
                AvailabilityBlock.end_at > start_at,
            )
        ).first()
        is not None
    )

def create_block_for_user(user_id, start_at, end_at):
    block = AvailabilityBlock(user_id=user_id, start_at=start_at, end_at=end_at)
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
