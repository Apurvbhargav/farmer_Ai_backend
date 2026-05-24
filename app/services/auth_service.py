from sqlalchemy.orm import Session

from app.db.models.farmer_model import Farmer

from app.core.security.hashing import (
    hash_password,
    verify_password
)

from app.core.security.jwt_handler import (
    create_access_token
)


def register_farmer(
    db: Session,
    full_name: str,
    phone_number: str,
    password: str,
    state_id: int,
    district_id: int,
    village_id: int
):

    existing_farmer = db.query(Farmer).filter(
        Farmer.phone_number == phone_number
    ).first()

    if existing_farmer:
        return None

    farmer = Farmer(
        full_name=full_name,
        phone_number=phone_number,
        hashed_password=hash_password(password),

        state_id=state_id,
        district_id=district_id,
        village_id=village_id
    )

    db.add(farmer)

    db.commit()

    db.refresh(farmer)

    return farmer


def login_farmer(
    db: Session,
    phone_number: str,
    password: str
):

    farmer = db.query(Farmer).filter(
        Farmer.phone_number == phone_number
    ).first()

    if not farmer:
        return None

    if not verify_password(
        password,
        farmer.hashed_password
    ):
        return None

    token = create_access_token({
        "farmer_id": farmer.id
    })

    return token