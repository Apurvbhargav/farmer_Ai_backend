from pydantic import BaseModel


class RegisterRequest(BaseModel):

    full_name: str

    phone_number: str

    password: str

    state_id: int

    district_id: int

    village_id: int


class LoginRequest(BaseModel):

    phone_number: str

    password: str