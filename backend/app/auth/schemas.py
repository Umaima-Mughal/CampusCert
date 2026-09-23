"""
app/auth/schemas.py

Pydantic models that define the shape of data going IN and OUT of the
auth API. FastAPI uses these to validate requests and format responses.

Whatever you put here should match what you write in docs/api-contracts.md
so the frontend team knows exactly what JSON to expect.
"""

import uuid
from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8)
    # Keep this set in sync with the roles seeded in
    # database/migrations/versions/0002_seed_default_roles.py
    role: Literal["student", "examiner", "admin"] = "student"
    organization_id: uuid.UUID | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True  # lets us build this from a SQLAlchemy model


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str