"""
app/auth/models.py

Database tables for authentication: User and Role.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.base_model import BaseModel


class Role(BaseModel):
    __tablename__ = "roles"

    # e.g. "student", "examiner", "admin", "super_admin"
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role")


class User(BaseModel):
    __tablename__ = "users"

    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    role = relationship("Role", back_populates="users")

    # Every user belongs to an organization (university/college) —
    # organizations/models.py defines the Organization table.
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )
