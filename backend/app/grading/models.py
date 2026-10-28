"""app/grading/models.py  (Member 4): the stored result of one attempt."""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.base_model import BaseModel
from app.attempts.models import (
    ExamAttempt,
    utcnow,
)  # noqa: F401  (ExamAttempt registers exam_attempts for the FK)


class Result(BaseModel):
    __tablename__ = "results"
    __table_args__ = (
        Index("ix_results_exam_id", "exam_id"),
        Index("ix_results_candidate_id", "candidate_id"),
    )

    attempt_id = Column(
        UUID(as_uuid=True),
        ForeignKey("exam_attempts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    # exam_id / candidate_id repeat what the attempt knows, so Member 5's analytics
    # can query results without joining through attempts.
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    total_marks = Column(Integer, nullable=False, default=0)
    obtained_marks = Column(Integer, nullable=False, default=0)
    correct_count = Column(Integer, nullable=False, default=0)
    incorrect_count = Column(Integer, nullable=False, default=0)
    unanswered_count = Column(Integer, nullable=False, default=0)
    percentage = Column(Float, nullable=False, default=0.0)
    passed = Column(Boolean, nullable=True)  # None when the exam has no passing score
    # per question: {"question_id", "position", "marks", "selected", "correct", "awarded", "gradable"}
    breakdown = Column(JSONB, nullable=False, default=list)
    graded_at = Column(DateTime, nullable=False, default=utcnow)
