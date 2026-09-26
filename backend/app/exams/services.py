"""
app/exams/services.py

Business rules for exam configuration, scheduling, lifecycle, and
candidate assignment. Routes stay thin and call these functions.
"""

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth.models import User, Role
from app.exams.constants import (
    ALLOWED_TRANSITIONS,
    STATUS_ACTIVE,
    STATUS_ARCHIVED,
    STATUS_CLOSED,
    STATUS_DRAFT,
    STATUS_SCHEDULED,
    STUDENT_ROLE,
)
from app.exams.models import Exam, ExamCandidate
from app.exams.schemas import ExamCreate, ExamSchedule, ExamUpdate
from app.organizations.models import Organization


def _forbidden(message: str = "You don't have permission to perform this action"):
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)


def _not_found(entity: str = "Exam"):
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity} not found")


def _bad_request(message: str):
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def can_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def resolve_organization_id(user: User, requested_org_id=None):
    """
    Tenant is always the authenticated user's organization.
    Frontend-supplied organization IDs are ignored for admin/examiner.
    """
    role_name = user.role.name
    if role_name in ("admin", "examiner"):
        if not user.organization_id:
            raise _bad_request("User is not assigned to an organization.")
        return user.organization_id

    if role_name == "super_admin":
        org_id = user.organization_id or requested_org_id
        if not org_id:
            raise _bad_request("User is not assigned to an organization.")
        return org_id

    raise _forbidden()


def assert_exam_access(user: User, exam: Exam) -> None:
    if user.role.name == "super_admin":
        return
    if user.role.name in ("admin", "examiner") and user.organization_id == exam.organization_id:
        return
    raise _not_found()


def get_exam_for_admin(db: Session, user: User, exam_id) -> Exam:
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise _not_found()
    assert_exam_access(user, exam)
    return exam


def _ensure_org_exists(db: Session, organization_id) -> None:
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org or not org.is_active:
        raise _bad_request("Organization not found or inactive")


def _validate_window(starts_at: datetime | None, ends_at: datetime | None, duration_minutes: int):
    if starts_at and ends_at and ends_at <= starts_at:
        raise _bad_request("ends_at must be after starts_at")
    if starts_at and ends_at:
        window_minutes = int((ends_at - starts_at).total_seconds() // 60)
        if window_minutes < duration_minutes:
            raise _bad_request(
                "The scheduled window is shorter than the exam duration"
            )


def create_exam(db: Session, user: User, payload: ExamCreate) -> Exam:
    organization_id = resolve_organization_id(user)
    _ensure_org_exists(db, organization_id)
    _validate_window(payload.starts_at, payload.ends_at, payload.duration_minutes)
    # Future subscription/entitlement checks (plan max vs payload.max_students)
    # belong here. This phase stores exam capacity only.

    status_value = STATUS_DRAFT
    if payload.starts_at and payload.ends_at:
        status_value = STATUS_SCHEDULED

    exam = Exam(
        organization_id=organization_id,
        created_by_user_id=user.id,
        name=payload.name.strip(),
        description=payload.description,
        instructions=payload.instructions,
        duration_minutes=payload.duration_minutes,
        status=status_value,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        passing_score=payload.passing_score,
        max_attempts=payload.max_attempts,
        shuffle_questions=payload.shuffle_questions,
        late_join_minutes=payload.late_join_minutes,
        max_students=payload.max_students,
        distribution=payload.distribution or {},
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


def list_exams(db: Session, user: User, status_filter: str | None = None) -> list[tuple[Exam, int]]:
    query = db.query(Exam, func.count(ExamCandidate.id).label("candidate_count")).outerjoin(
        ExamCandidate, ExamCandidate.exam_id == Exam.id
    )

    if user.role.name in ("admin", "examiner"):
        if not user.organization_id:
            return []
        query = query.filter(Exam.organization_id == user.organization_id)
    elif user.role.name != "super_admin":
        raise _forbidden()

    if status_filter:
        query = query.filter(Exam.status == status_filter)

    rows = (
        query.group_by(Exam.id)
        .order_by(Exam.created_at.desc())
        .all()
    )
    return [(exam, int(count or 0)) for exam, count in rows]


def update_exam(db: Session, exam: Exam, payload: ExamUpdate) -> Exam:
    if exam.status in {STATUS_ACTIVE, STATUS_CLOSED, STATUS_ARCHIVED}:
        raise _bad_request(
            f"An exam in {exam.status} status cannot be reconfigured"
        )

    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        data["name"] = data["name"].strip()
    if "max_students" in data and data["max_students"] is not None:
        assigned = candidate_count(db, exam.id)
        if data["max_students"] < assigned:
            raise _bad_request(
                f"Maximum students cannot be below the {assigned} candidate(s) already assigned"
            )

    for field, value in data.items():
        setattr(exam, field, value)

    _validate_window(exam.starts_at, exam.ends_at, exam.duration_minutes)

    if exam.status == STATUS_DRAFT and exam.starts_at and exam.ends_at:
        exam.status = STATUS_SCHEDULED

    db.commit()
    db.refresh(exam)
    return exam


def schedule_exam(db: Session, exam: Exam, payload: ExamSchedule) -> Exam:
    if exam.status in {STATUS_CLOSED, STATUS_ARCHIVED}:
        raise _bad_request(f"Cannot schedule an exam in {exam.status} status")
    if exam.status == STATUS_ACTIVE:
        raise _bad_request("Deactivate or close the exam before changing its schedule")

    _validate_window(payload.starts_at, payload.ends_at, exam.duration_minutes)
    exam.starts_at = payload.starts_at
    exam.ends_at = payload.ends_at
    if not can_transition(exam.status, STATUS_SCHEDULED) and exam.status != STATUS_SCHEDULED:
        raise _bad_request(f"Cannot move exam from {exam.status} to {STATUS_SCHEDULED}")
    exam.status = STATUS_SCHEDULED
    db.commit()
    db.refresh(exam)
    return exam


def change_exam_status(db: Session, exam: Exam, target: str) -> Exam:
    if exam.status == target:
        return exam
    if not can_transition(exam.status, target):
        raise _bad_request(f"Cannot move exam from {exam.status} to {target}")

    if target == STATUS_ACTIVE:
        if exam.duration_minutes < 1:
            raise _bad_request("Duration must be set before activating an exam")
        if exam.starts_at and exam.ends_at:
            _validate_window(exam.starts_at, exam.ends_at, exam.duration_minutes)

    if target == STATUS_DRAFT:
        exam.starts_at = None
        exam.ends_at = None

    exam.status = target
    db.commit()
    db.refresh(exam)
    return exam


def deactivate_exam(db: Session, exam: Exam) -> Exam:
    """Take a live or scheduled exam out of the student-facing window."""
    if exam.status == STATUS_ACTIVE:
        target = STATUS_SCHEDULED if exam.starts_at and exam.ends_at else STATUS_DRAFT
        return change_exam_status(db, exam, target)
    if exam.status == STATUS_SCHEDULED:
        return change_exam_status(db, exam, STATUS_DRAFT)
    raise _bad_request("Only scheduled or active exams can be deactivated")


def delete_exam(db: Session, exam: Exam) -> None:
    if exam.status != STATUS_DRAFT:
        raise _bad_request("Only draft exams can be deleted")
    db.delete(exam)
    db.commit()


def exam_summary(db: Session, user: User) -> dict:
    query = db.query(Exam.status, func.count(Exam.id))
    if user.role.name in ("admin", "examiner"):
        if not user.organization_id:
            return {"total": 0, "by_status": {}, "upcoming": 0}
        query = query.filter(Exam.organization_id == user.organization_id)
    elif user.role.name != "super_admin":
        raise _forbidden()

    rows = query.group_by(Exam.status).all()
    by_status = {status_name: int(count) for status_name, count in rows}
    total = sum(by_status.values())

    upcoming_query = db.query(func.count(Exam.id)).filter(
        Exam.status == STATUS_SCHEDULED
    )
    if user.role.name in ("admin", "examiner") and user.organization_id:
        upcoming_query = upcoming_query.filter(Exam.organization_id == user.organization_id)
    upcoming = int(upcoming_query.scalar() or 0)
    return {"total": total, "by_status": by_status, "upcoming": upcoming}


def list_eligible_candidates(db: Session, user: User) -> list[User]:
    organization_id = resolve_organization_id(user, user.organization_id)
    return (
        db.query(User)
        .join(Role, User.role_id == Role.id)
        .options(joinedload(User.role))
        .filter(
            User.organization_id == organization_id,
            Role.name == STUDENT_ROLE,
            User.is_active.is_(True),
        )
        .order_by(User.full_name.asc())
        .all()
    )


def list_exam_candidates(db: Session, exam: Exam) -> list[User]:
    return (
        db.query(User)
        .join(ExamCandidate, ExamCandidate.user_id == User.id)
        .options(joinedload(User.role))
        .filter(ExamCandidate.exam_id == exam.id)
        .order_by(User.full_name.asc())
        .all()
    )


def assign_candidates(db: Session, exam: Exam, user_ids: list) -> list[User]:
    if exam.status == STATUS_ARCHIVED:
        raise _bad_request("Cannot assign candidates to an archived exam")

    unique_ids = list(dict.fromkeys(user_ids))
    students = (
        db.query(User)
        .join(Role, User.role_id == Role.id)
        .filter(
            User.id.in_(unique_ids),
            User.organization_id == exam.organization_id,
            Role.name == STUDENT_ROLE,
            User.is_active.is_(True),
        )
        .all()
    )
    found_ids = {student.id for student in students}
    missing = [str(uid) for uid in unique_ids if uid not in found_ids]
    if missing:
        raise _bad_request(
            "One or more users are not active students in this organization"
        )

    existing = {
        row.user_id
        for row in db.query(ExamCandidate.user_id).filter(
            ExamCandidate.exam_id == exam.id,
            ExamCandidate.user_id.in_(unique_ids),
        )
    }
    new_ids = [student.id for student in students if student.id not in existing]
    assigned = candidate_count(db, exam.id)
    if assigned + len(new_ids) > exam.max_students:
        raise _bad_request(
            f"This exam allows at most {exam.max_students} students "
            f"({assigned} already assigned)."
        )
    for student_id in new_ids:
        db.add(ExamCandidate(exam_id=exam.id, user_id=student_id))

    db.commit()
    return list_exam_candidates(db, exam)


def remove_candidate(db: Session, exam: Exam, user_id) -> None:
    row = (
        db.query(ExamCandidate)
        .filter(ExamCandidate.exam_id == exam.id, ExamCandidate.user_id == user_id)
        .first()
    )
    if not row:
        raise _not_found("Candidate")
    db.delete(row)
    db.commit()


def candidate_count(db: Session, exam_id) -> int:
    return int(
        db.query(func.count(ExamCandidate.id))
        .filter(ExamCandidate.exam_id == exam_id)
        .scalar()
        or 0
    )


