
"""Secure exam integrity and examiner action endpoints."""

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import require_role
from app.auth.models import User
from app.attempts.models import ExamAttempt
from app.attempts import services as attempt_services
from app.attempts.constants import (
    ATTEMPT_ACTIVE,
    ATTEMPT_FROZEN,
    FINISHED_STATUSES,
)
from app.exams.models import Exam

from .models import ExamEvent


router = APIRouter(prefix="/api", tags=["integrity"])

student_only = require_role("student")
staff_only = require_role("examiner", "admin", "super_admin")

INTEGRITY_EVENTS = {
    "TAB_SWITCH",
    "FULLSCREEN_EXIT",
    "COPY_PASTE",
}

# Security policy: automatically freeze on these event types.
FREEZE_ON = {
    "FULLSCREEN_EXIT",
    "COPY_PASTE",
}

DUPLICATE_COOLDOWN_SECONDS = 3


class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempt_id: uuid.UUID
    type: str


class ActionIn(BaseModel):
    reason: str | None = None


def get_staff_attempt(db, user, attempt_id):
    """Get an attempt while enforcing staff organization access."""

    query = db.query(ExamAttempt).filter(
        ExamAttempt.id == attempt_id
    )

    if user.role.name != "super_admin":
        query = query.join(
            Exam,
            Exam.id == ExamAttempt.exam_id,
        ).filter(
            Exam.organization_id == user.organization_id
        )

    attempt = query.with_for_update().first()

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail="Attempt not found",
        )

    return attempt


@router.post("/events", status_code=201)
def record_integrity_event(
    body: EventIn,
    db: Session = Depends(get_db),
    user: User = Depends(student_only),
):
    if body.type not in INTEGRITY_EVENTS:
        raise HTTPException(
            status_code=422,
            detail="Unsupported integrity event",
        )

    attempt = (
        db.query(ExamAttempt)
        .filter(
            ExamAttempt.id == body.attempt_id,
            ExamAttempt.candidate_id == user.id,
        )
        .with_for_update()
        .first()
    )

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail="Attempt not found",
        )

    attempt_services.finish_if_time_is_up(db, attempt)

    if attempt.status in FINISHED_STATUSES:
        raise HTTPException(
            status_code=409,
            detail="Attempt already finalized",
        )

    if attempt.status not in (
        ATTEMPT_ACTIVE,
        ATTEMPT_FROZEN,
    ):
        raise HTTPException(
            status_code=409,
            detail="Attempt is not open",
        )

    # Use server time instead of a client-controlled timestamp.
    now = datetime.utcnow()
    cutoff = now - timedelta(
        seconds=DUPLICATE_COOLDOWN_SECONDS
    )

    # Check the latest occurrence of this event type.
    latest_event = (
        db.query(ExamEvent)
        .filter(
            ExamEvent.attempt_id == attempt.id,
            ExamEvent.actor_id == user.id,
            ExamEvent.event_type == body.type,
        )
        .order_by(ExamEvent.occurred_at.desc())
        .first()
    )

    # Suppress only repeated identical events.
    if (
        latest_event is not None
        and latest_event.occurred_at >= cutoff
    ):
        return {
            "recorded": False,
            "duplicate": True,
            "status": attempt.status,
            "frozen": attempt.status == ATTEMPT_FROZEN,
        }

    event = ExamEvent(
        attempt_id=attempt.id,
        actor_id=user.id,
        event_type=body.type,
        occurred_at=now,
    )
    db.add(event)

    if (
        body.type in FREEZE_ON
        and attempt.status == ATTEMPT_ACTIVE
    ):
        attempt.status = ATTEMPT_FROZEN

        db.add(
            ExamEvent(
                attempt_id=attempt.id,
                actor_id=user.id,
                event_type="FROZEN",
                occurred_at=now,
                note="Configured integrity policy",
            )
        )

    db.commit()

    return {
        "recorded": True,
        "duplicate": False,
        "status": attempt.status,
        "frozen": attempt.status == ATTEMPT_FROZEN,
    }


@router.post("/attempts/{attempt_id}/resume")
def resume_attempt(
    attempt_id: uuid.UUID,
    body: ActionIn | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
):
    attempt = get_staff_attempt(
        db,
        user,
        attempt_id,
    )

    attempt_services.finish_if_time_is_up(db, attempt)

    if attempt.status != ATTEMPT_FROZEN:
        raise HTTPException(
            status_code=409,
            detail="Only frozen attempts can be resumed",
        )

    attempt.status = ATTEMPT_ACTIVE

    db.add(
        ExamEvent(
            attempt_id=attempt.id,
            actor_id=user.id,
            event_type="RESUMED",
            note=body.reason if body else None,
        )
    )

    db.commit()

    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
    }


@router.post("/attempts/{attempt_id}/terminate")
def terminate_attempt(
    attempt_id: uuid.UUID,
    body: ActionIn | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
):
    attempt = get_staff_attempt(
        db,
        user,
        attempt_id,
    )

    attempt_services.finish_if_time_is_up(db, attempt)

    if attempt.status in FINISHED_STATUSES:
        raise HTTPException(
            status_code=409,
            detail="Attempt already finalized",
        )

    if attempt.status not in (
        ATTEMPT_ACTIVE,
        ATTEMPT_FROZEN,
    ):
        raise HTTPException(
            status_code=409,
            detail="Attempt is not open",
        )

    db.add(
        ExamEvent(
            attempt_id=attempt.id,
            actor_id=user.id,
            event_type="TERMINATED",
            note=body.reason if body else None,
        )
    )

    db.flush()

    attempt_services.finalize_attempt(
        db,
        attempt,
        "TERMINATED",
    )

    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
    }
