from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from jose import jwt, JWTError

from app.config import (
    JWT_SECRET,
    JWT_ALGORITHM
)

security = HTTPBearer()


def get_current_farmer(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        farmer_id = payload.get("farmer_id")

        if farmer_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return farmer_id

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )