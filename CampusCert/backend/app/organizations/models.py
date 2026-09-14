"""
app/organizations/models.py

An Organization = a university/college/institute using the platform.
Users belong to an Organization (see app/auth/models.py -> organization_id).
"""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.core.base_model import BaseModel


class Organization(BaseModel):
    __tablename__ = "organizations"

    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)  # e.g. "cust-university"
    contact_email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Note: linked from the User side (auth/models.py) via organization_id,
    # not a direct relationship() here, to avoid a circular import between
    # auth <-> organizations. If you need `.users` on Organization later,
    # define it with a string reference and coordinate with the team first.
