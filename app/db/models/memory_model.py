from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Integer,
    TIMESTAMP,
    ForeignKey,
    Text
)

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from pgvector.sqlalchemy import Vector

from app.db.session import Base


class FarmerMemoryEvent(Base):

    __tablename__ = "farmer_memory_events"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True
    )

    farmer_id = Column(
        BigInteger,
        ForeignKey("farmers.id"),
        nullable=False,
        index=True
    )

    event_type = Column(
        String,
        nullable=False,
        index=True
    )

    crop_name = Column(
        String,
        nullable=True,
        index=True
    )

    crop_cycle_id = Column(
        String,
        nullable=True,
        index=True
    )

    event_time = Column(
        TIMESTAMP,
        nullable=True
    )

    details = Column(
        JSONB,
        nullable=False,
        default={}
    )

    memory_text = Column(
        Text,
        nullable=True
    )

    embedding = Column(
        Vector(3072),
        nullable=True
    )

    source_query = Column(
        Text,
        nullable=True
    )

    confidence = Column(
        Integer,
        nullable=True
    )

    importance_score = Column(
        Integer,
        default=50
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )