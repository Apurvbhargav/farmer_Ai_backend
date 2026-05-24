from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Integer
)

from app.db.session import Base


class Farmer(Base):

    __tablename__ = "farmers"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True
    )

    full_name = Column(
        String,
        nullable=False
    )

    phone_number = Column(
        String,
        unique=True,
        nullable=False
    )

    hashed_password = Column(
        String,
        nullable=False
    )

    state_id = Column(
        Integer,
        nullable=False
    )

    district_id = Column(
        Integer,
        nullable=False
    )

    village_id = Column(
        Integer,
        nullable=False
    )