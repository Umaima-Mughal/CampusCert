"""
app/organizations/schemas.py

Request/response shapes for the organizations API.
"""

import uuid
from pydantic import BaseModel, EmailStr, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=100)
    contact_email: EmailStr | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = None
    contact_email: EmailStr | None = None
    is_active: bool | None = None


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    contact_email: EmailStr | None
    is_active: bool

    class Config:
        from_attributes = True
