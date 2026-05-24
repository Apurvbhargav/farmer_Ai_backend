from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.api.schemas.auth_schema import (
    RegisterRequest,
    LoginRequest
)

from app.services.auth_service import (
    register_farmer,
    login_farmer
)

from app.db.session import SessionLocal

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@router.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):

    farmer = register_farmer(
        db,
        request.full_name,
        request.phone_number,
        request.password,
        request.state_id,
        request.district_id,
        request.village_id
    )

    if not farmer:
        return {
            "message": "Phone number already exists"
        }

    return {
        "message": "Farmer registered successfully"
    }


@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):

    token = login_farmer(
        db,
        request.phone_number,
        request.password
    )

    if not token:
        return {
            "message": "Invalid credentials"
        }

    return {
        "access_token": token
    }