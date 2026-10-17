import hashlib

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def question_hash(subject: str, topic: str, question: str) -> str:
    """Same question under the same subject/topic = duplicate, whatever the casing/spacing."""
    key = "|".join(s.strip().lower() for s in (subject, topic, question))
    return hashlib.sha256(key.encode()).hexdigest()


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(120), nullable=False, index=True)
    difficulty = Column(String(10), nullable=False, index=True)  # easy | medium | hard
    topic = Column(String(160), nullable=False, index=True)
    question = Column(Text, nullable=False)
    # Multiple-choice: four options, exactly one correct, plus an optional worked solution.
    # Nullable so older questions (imported before MCQ support) keep working.
    option_a = Column(Text, nullable=True)
    option_b = Column(Text, nullable=True)
    option_c = Column(Text, nullable=True)
    option_d = Column(Text, nullable=True)
    correct_option = Column(String(1), nullable=True)   # "A" | "B" | "C" | "D"
    solution = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=False)
    # Which university/college owns this question (organizations.id). Questions are
    # private to their organization, like exams are.
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    created_by = Column(Integer, nullable=True)      # teacher user id (fill from auth)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # the same question may exist once per organization
    __table_args__ = (UniqueConstraint("organization_id", "content_hash", name="uq_questions_org_content_hash"),)


class ExamPaper(Base):
    """A set of questions a teacher put together by hand or by the random generator.
    (An exam attaches a paper through exams.paper_id.)"""
    __tablename__ = "exam_papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    instructions = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    created_by = Column(Integer, nullable=True)      # teacher user id (fill from auth)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("ExamPaperItem", cascade="all, delete-orphan",
                         order_by="ExamPaperItem.position")


class ExamPaperItem(Base):
    __tablename__ = "exam_paper_items"

    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey("exam_papers.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    marks = Column(Integer, nullable=False, default=1)

    question = relationship("Question")

    __table_args__ = (UniqueConstraint("paper_id", "question_id", name="uq_paper_question"),)
