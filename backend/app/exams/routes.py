"""
app/exams/routes.py

University/admin exam-management endpoints:
  GET    /api/exams/summary
  GET    /api/exams/eligible-candidates
  POST   /api/exams
  GET    /api/exams
  GET    /api/exams/{exam_id}
  PATCH  /api/exams/{exam_id}
  DELETE /api/exams/{exam_id}
  POST   /api/exams/{exam_id}/schedule
  POST   /api/exams/{exam_id}/activate
  POST   /api/exams/{exam_id}/deactivate
  POST   /api/exams/{exam_id}/close
  POST   /api/exams/{exam_id}/archive
  GET    /api/exams/{exam_id}/candidates
  POST   /api/exams/{exam_id}/candidates
  DELETE /api/exams/{exam_id}/candidates/{user_id}
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.auth.models import User
from app.core.database import get_db
from app.exams.constants import ADMIN_ROLES, STATUS_ACTIVE, STATUS_ARCHIVED, STATUS_CLOSED
from app.exams.schemas import (
    CandidateOut,
    ExamCandidateAssign,
    ExamCreate,
    ExamOut,
    ExamSchedule,
    ExamStatusChangeOut,
    ExamSummaryOut,
    ExamUpdate,
    serialize_exam,
)
from app.exams import services

router = APIRouter(prefix="/api/exams", tags=["exams"])

admin_user = require_role(*ADMIN_ROLES)


def _candidate_out(user: User) -> CandidateOut:
    return CandidateOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role.name,
        is_active=user.is_active,
    )


@router.get("/summary", response_model=ExamSummaryOut)
def get_exam_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    return services.exam_summary(db, current_user)


@router.get("/eligible-candidates", response_model=list[CandidateOut])
def get_eligible_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    students = services.list_eligible_candidates(db, current_user)
    return [_candidate_out(student) for student in students]


@router.post("", response_model=ExamOut, status_code=status.HTTP_201_CREATED)
def create_exam(
    payload: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    exam = services.create_exam(db, current_user, payload)
    return serialize_exam(exam, 0)


@router.get("", response_model=list[ExamOut])
def list_exams(
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    rows = services.list_exams(db, current_user, status_filter)
    return [serialize_exam(exam, count) for exam, count in rows]


@router.get("/{exam_id}", response_model=ExamOut)
def get_exam(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    exam = services.get_exam_for_admin(db, current_user, exam_id)
    return serialize_exam(exam, services.candidate_count(db, exam.id))


@router.patch("/{exam_id}", response_model=ExamOut)
def update_exam(
    exam_id: uuid.UUID,
    payload: ExamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    exam = services.get_exam_for_admin(db, current_user, exam_id)
    exam = services.update_exam(db, exam, payload)
    return serialize_exam(exam, services.candidate_count(db, exam.id))


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    exam = services.get_exam_for_admin(db, current_user, exam_id)
    services.delete_exam(db, exam)


@router.post("/{exam_id}/schedule", response_model=ExamOut)
def schedule_exam(
    exam_id: uuid.UUID,
    payload: ExamSchedule,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    exam = services.get_exam_for_admin(db, current_user, exam_id)
    exam = services.schedule_exam(db, exam, payload)
    return serialize_exam(exam, services.candidate_count(db, exam.id))


@router.post("/{exam_id}/activate", response_model=ExamStatusChangeOut)
def activate_exam(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    exam = services.get_exam_for_admin(db, current_user, exam_id)
    exam = services.change_exam_status(db, exam, STATUS_ACTIVE)
    return ExamStatusChangeOut(id=exam.id, status=exam.status, is_active=True)


@router.post("/{exam_id}/deactivate", response_model=ExamStatusChangeOut)
def deactivate_exam(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    exam = services.get_exam_for_admin(db, current_user, exam_id)
    exam = services.deactivate_exam(db, exam)
    return ExamStatusChangeOut(
        id=exam.id, status=exam.status, is_active=exam.status == STATUS_ACTIVE
    )


@router.post("/{exam_id}/close", response_model=ExamStatusChangeOut)
def close_exam(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    exam = services.get_exam_for_admin(db, current_user, exam_id)
    exam = services.change_exam_status(db, exam, STATUS_CLOSED)
    return ExamStatusChangeOut(id=exam.id, status=exam.status, is_active=False)


@router.post("/{exam_id}/archive", response_model=ExamStatusChangeOut)
def archive_exam(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    exam = services.get_exam_for_admin(db, current_user, exam_id)
    exam = services.change_exam_status(db, exam, STATUS_ARCHIVED)
    return ExamStatusChangeOut(id=exam.id, status=exam.status, is_active=False)


@router.get("/{exam_id}/candidates", response_model=list[CandidateOut])
def get_exam_candidates(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    exam = services.get_exam_for_admin(db, current_user, exam_id)
    return [_candidate_out(user) for user in services.list_exam_candidates(db, exam)]


@router.post("/{exam_id}/candidates", response_model=list[CandidateOut])
def assign_exam_candidates(
    exam_id: uuid.UUID,
    payload: ExamCandidateAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    exam = services.get_exam_for_admin(db, current_user, exam_id)
    students = services.assign_candidates(db, exam, payload.user_ids)
    return [_candidate_out(user) for user in students]


@router.delete("/{exam_id}/candidates/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_exam_candidate(
    exam_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_user),
):
    exam = services.get_exam_for_admin(db, current_user, exam_id)
    services.remove_candidate(db, exam, user_id)
