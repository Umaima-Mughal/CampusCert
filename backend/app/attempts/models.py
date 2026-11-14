"""
app/attempts/models.py  (Member 4)

ExamAttempt      one student's sitting of one exam (frozen copy of the questions in `layout`)
CandidateAnswer  the student's CURRENT answer per question (autosave overwrites it)
AnswerLog        every save, never overwritten: this is the audit trail of answers
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.base_model import BaseModel
from app.exams.models import Exam  # noqa: F401  (registers exams for the FK)


def utcnow() -> datetime:
    """Current UTC time without a timezone (the database stores naive UTC times)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ExamAttempt(BaseModel):
    __tablename__ = "exam_attempts"
    __table_args__ = (
        UniqueConstraint("exam_id", "candidate_id", "attempt_number", name="uq_attempt_exam_candidate_number"),
        Index("ix_exam_attempts_exam_id", "exam_id"),
        Index("ix_exam_attempts_candidate_id", "candidate_id"),
    )

    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    attempt_number = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="ACTIVE")
    started_at = Column(DateTime, nullable=False, default=utcnow)
    expires_at = Column(DateTime, nullable=False)
    submitted_at = Column(DateTime, nullable=True)

    # Snapshot taken when the attempt starts, so later edits to the paper or the
    # question bank cannot change this student's exam or grade:
    # {"questions": [{"id": 12, "marks": 1, "correct": "B", "options": ["C","A","B","D"]}, ...]}
    # The list order is the order the student sees. "correct" never leaves the server.
    layout = Column(JSONB, nullable=False, default=dict)


class CandidateAnswer(BaseModel):
    __tablename__ = "candidate_answers"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_candidate_answer_attempt_question"),
        Index("ix_candidate_answers_attempt_id", "attempt_id"),
    )

    attempt_id = Column(UUID(as_uuid=True), ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, nullable=False)  # no FK on purpose, see migration 0008
    selected_option = Column(String(1), nullable=True)  # "A" | "B" | "C" | "D" | None
    marked_for_review = Column(Boolean, nullable=False, default=False)
    answered_at = Column(DateTime, nullable=True)


class AnswerLog(BaseModel):
    __tablename__ = "answer_log"
    __table_args__ = (Index("ix_answer_log_attempt_id", "attempt_id"),)

    attempt_id = Column(UUID(as_uuid=True), ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, nullable=False)
    selected_option = Column(String(1), nullable=True)
    marked_for_review = Column(Boolean, nullable=False, default=False)
    saved_at = Column(DateTime, nullable=False, default=utcnow)
