"""
app/exams/schemas.py

Request/response shapes for the exam-management API.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.exams.constants import STATUS_DRAFT, MAX_STUDENTS_HARD_CAP


class ExamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    duration_minutes: int = Field(..., ge=1, le=600)
    description: str | None = Field(None, max_length=2000)
    instructions: str | None = Field(None, max_length=5000)
    distribution: dict[str, int] = Field(default_factory=dict)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    passing_score: int | None = Field(None, ge=0, le=100)
    max_attempts: int = Field(1, ge=1, le=10)
    shuffle_questions: bool = True
    late_join_minutes: int = Field(0, ge=0, le=180)
    max_students: int = Field(..., ge=1, le=MAX_STUDENTS_HARD_CAP)

    @field_validator("distribution")
    @classmethod
    def distribution_counts_must_be_positive(cls, value: dict[str, int]) -> dict[str, int]:
        cleaned: dict[str, int] = {}
        for subject_id, count in value.items():
            key = str(subject_id).strip()
            if not key:
                raise ValueError("distribution keys must be non-empty subject ids")
            if int(count) < 1:
                raise ValueError("distribution counts must be at least 1")
            cleaned[key] = int(count)
        return cleaned


class ExamUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    duration_minutes: int | None = Field(None, ge=1, le=600)
    description: str | None = Field(None, max_length=2000)
    instructions: str | None = Field(None, max_length=5000)
    distribution: dict[str, int] | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    passing_score: int | None = Field(None, ge=0, le=100)
    max_attempts: int | None = Field(None, ge=1, le=10)
    shuffle_questions: bool | None = None
    late_join_minutes: int | None = Field(None, ge=0, le=180)
    max_students: int | None = Field(None, ge=1, le=MAX_STUDENTS_HARD_CAP)

    @field_validator("distribution")
    @classmethod
    def distribution_counts_must_be_positive(
        cls, value: dict[str, int] | None
    ) -> dict[str, int] | None:
        if value is None:
            return value
        return ExamCreate.distribution_counts_must_be_positive(value)


class ExamSchedule(BaseModel):
    starts_at: datetime
    ends_at: datetime


class ExamCandidateAssign(BaseModel):
    user_ids: list[uuid.UUID] = Field(..., min_length=1)


class CandidateOut(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class ExamOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_by_user_id: uuid.UUID
    name: str
    description: str | None
    instructions: str | None
    duration_minutes: int
    status: str
    starts_at: datetime | None
    ends_at: datetime | None
    passing_score: int | None
    max_attempts: int
    shuffle_questions: bool
    late_join_minutes: int
    max_students: int
    distribution: dict[str, int]
    is_active: bool
    candidate_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExamSummaryOut(BaseModel):
    total: int
    by_status: dict[str, int]
    upcoming: int


class ExamStatusChangeOut(BaseModel):
    id: uuid.UUID
    status: str = STATUS_DRAFT
    is_active: bool = False


def serialize_exam(exam, candidate_count: int | None = None) -> ExamOut:
    count = candidate_count
    if count is None:
        count = len(exam.candidates) if getattr(exam, "candidates", None) is not None else 0
    return ExamOut(
        id=exam.id,
        organization_id=exam.organization_id,
        created_by_user_id=exam.created_by_user_id,
        name=exam.name,
        description=exam.description,
        instructions=exam.instructions,
        duration_minutes=exam.duration_minutes,
        status=exam.status,
        starts_at=exam.starts_at,
        ends_at=exam.ends_at,
        passing_score=exam.passing_score,
        max_attempts=exam.max_attempts,
        shuffle_questions=exam.shuffle_questions,
        late_join_minutes=exam.late_join_minutes,
        max_students=exam.max_students,
        distribution=exam.distribution or {},
        is_active=exam.status == "ACTIVE",
        candidate_count=count,
        created_at=exam.created_at,
        updated_at=exam.updated_at,
    )
