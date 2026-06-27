from sqlalchemy import (
    Column,
    BigInteger,
    Text,
    String,
    TIMESTAMP,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.db.session import Base


class FarmerConversation(Base):
    __tablename__ = "farmer_conversations"

    id = Column(BigInteger, primary_key=True, index=True)

    farmer_id = Column(
        BigInteger,
        ForeignKey("farmers.id"),
        nullable=False,
        index=True
    )

    original_query = Column(Text, nullable=False)

    status = Column(String, default="active")  # active | waiting | completed

    analysis = Column(JSONB, default={})

    retrieved_memories = Column(JSONB, default=[])

    followup_answers = Column(JSONB, default={})

    current_question = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())

    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())