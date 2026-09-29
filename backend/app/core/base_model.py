"""
app/core/base_model.py

A shared base class every table's model can inherit from, so we don't
repeat "id, created_at, updated_at" in every single model file.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class BaseModel(Base):
    """
    Abstract base — not a real table itself.
    Other models do:  class User(BaseModel): __tablename__ = "users"
    """
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
