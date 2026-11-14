
"""Exam integrity events and examiner decisions."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.base_model import BaseModel
from app.attempts.models import utcnow


class ExamEvent(BaseModel):
    __tablename__ = "exam_events"

    __table_args__ = (
        Index(
            "ix_exam_events_attempt_time",
            "attempt_id",
            "occurred_at",
        ),
    )

    attempt_id = Column(
        UUID(as_uuid=True),
        ForeignKey("exam_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )

    actor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    event_type = Column(
        String(40),
        nullable=False,
    )

    occurred_at = Column(
        DateTime,
        nullable=False,
        default=utcnow,
    )

    note = Column(
        Text,
        nullable=True,
    )
