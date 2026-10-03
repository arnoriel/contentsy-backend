import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field

NormalizedEmail = Annotated[EmailStr, AfterValidator(lambda v: v.strip().lower())]
LoginEmail = Annotated[str, Field(min_length=3, max_length=254), AfterValidator(lambda v: v.strip().lower())]


class RegisterRequest(BaseModel):
    email: NormalizedEmail
    # max 128: batasi biaya hashing (anti DoS). Argon2 tidak punya limit 72 byte seperti bcrypt.
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: LoginEmail
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    credits: int
    created_at: datetime


class CreditsOut(BaseModel):
    credits: int
