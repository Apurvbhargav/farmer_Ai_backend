from sqlalchemy.orm import Session

from app.db.models.memory_model import (
    FarmerMemoryEvent
)


def save_memory_event(
    db: Session,
    farmer_id: int,
    event_type: str,
    crop_name: str = None,
    details: dict = None,
    source_query: str = None,
    confidence: int = None
):

    memory = FarmerMemoryEvent(
        farmer_id=farmer_id,
        event_type=event_type,
        crop_name=crop_name,
        details=details or {},
        source_query=source_query,
        confidence=confidence
    )

    db.add(memory)

    db.commit()

    db.refresh(memory)

    return memory


def get_recent_memory(
    db: Session,
    farmer_id: int,
    limit: int = 10
):

    return (
        db.query(FarmerMemoryEvent)
        .filter(
            FarmerMemoryEvent.farmer_id == farmer_id
        )
        .order_by(
            FarmerMemoryEvent.created_at.desc()
        )
        .limit(limit)
        .all()
    )