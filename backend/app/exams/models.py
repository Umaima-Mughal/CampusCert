"""
app/exams/models.py

Exam configuration owned by a university organization.
Question content itself belongs to Member 3; attempt rows belong to
Member 4. This module stores the exam record, schedule, and assigned
candidates so those modules can attach later.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.base_model import BaseModel


class Exam(BaseModel):
    __tablename__ = "exams"
    __table_args__ = (
        Index("ix_exams_organization_id", "organization_id"),
        Index("ix_exams_organization_status", "organization_id", "status"),
    )

    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    created_by_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    name = Column(String(200), nullable=False)
    description = Column(String(2000), nullable=True)
    instructions = Column(String(5000), nullable=True)
    duration_minutes = Column(Integer, nullable=False)

    status = Column(String(20), nullable=False, default="DRAFT")
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)

    passing_score = Column(Integer, nullable=True)
    max_attempts = Column(Integer, nullable=False, default=1)
    shuffle_questions = Column(Boolean, nullable=False, default=True)
    late_join_minutes = Column(Integer, nullable=False, default=0)

    # Subject/topic counts for Member 3 random selection, e.g.
    # { "<subject_uuid>": 10 }. Empty until the question bank exists.
    distribution = Column(JSONB, nullable=False, default=dict)

    candidates = relationship(
        "ExamCandidate",
        back_populates="exam",
        cascade="all, delete-orphan",
    )


class ExamCandidate(BaseModel):
    __tablename__ = "exam_candidates"
    __table_args__ = (
        UniqueConstraint("exam_id", "user_id", name="uq_exam_candidates_exam_user"),
        Index("ix_exam_candidates_exam_id", "exam_id"),
        Index("ix_exam_candidates_user_id", "user_id"),
    )

    exam_id = Column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    exam = relationship("Exam", back_populates="candidates")
