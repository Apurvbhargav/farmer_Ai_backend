from sqlalchemy.orm import Session

from app.db.models.memory_model import (
    FarmerMemoryEvent
)

from datetime import datetime

from app.services.embedding_service import (
    generate_embedding
)

from app.services.memory_text_builder import (
    build_memory_text
)


def save_memory_event(
    db,
    farmer_id,
    event_type,
    crop_name=None,
    details=None,
    source_query=None,
    confidence=None
):

    details = details or {}

    memory_text = build_memory_text(
    crop_name=crop_name,
    event_type=event_type,
    details=details,
    source_query=source_query
)

    embedding = generate_embedding(
        memory_text
    )

    crop_cycle_id = None

    if crop_name:

        crop_cycle_id = (
            f"{crop_name.lower()}_{datetime.now().year}"
        )

    memory = FarmerMemoryEvent(

        farmer_id=farmer_id,

        event_type=event_type,

        crop_name=crop_name,

        crop_cycle_id=crop_cycle_id,

        details=details,

        memory_text=memory_text,

        embedding=embedding,

        source_query=source_query,

        confidence=confidence,

        importance_score=80
    )

    db.add(memory)

    db.commit()

    db.refresh(memory)

    return memory