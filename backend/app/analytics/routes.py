"""Exam statistics and integrity event timeline."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.auth.models import User
from app.core.database import get_db
from app.exams.models import Exam
from app.attempts.models import ExamAttempt, AnswerLog
from app.security.models import ExamEvent
from app.grading.models import Result
from collections import defaultdict
from app.auth.models import User as SecurityUser


router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"],
)

staff_only = require_role("examiner", "admin", "super_admin")


def get_authorized_exam(db, user, exam_id):
    query = db.query(Exam).filter(Exam.id == exam_id)

    if user.role.name != "super_admin":
        query = query.filter(Exam.organization_id == user.organization_id)

    exam = query.first()

    if exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found",
        )

    return exam


@router.get("/exams/{exam_id}/overview")
def exam_overview(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
):
    get_authorized_exam(db, user, exam_id)

    attempts = db.query(ExamAttempt).filter(ExamAttempt.exam_id == exam_id).all()

    attempt_ids = [a.id for a in attempts]

    flagged = set()

    if attempt_ids:
        event_rows = (
            db.query(ExamEvent.attempt_id)
            .filter(
                ExamEvent.attempt_id.in_(attempt_ids),
                ExamEvent.event_type.in_(
                    [
                        "TAB_SWITCH",
                        "FULLSCREEN_EXIT",
                        "COPY_PASTE",
                    ]
                ),
            )
            .distinct()
            .all()
        )

        flagged = {row[0] for row in event_rows}

    return {
        "total_candidates": len({a.candidate_id for a in attempts}),
        "active": sum(a.status == "ACTIVE" for a in attempts),
        "completed": sum(a.status in ("SUBMITTED", "TERMINATED") for a in attempts),
        "frozen": sum(a.status == "FROZEN" for a in attempts),
        "flagged": len(flagged),
    }


@router.get("/attempts/{attempt_id}/timeline")
def attempt_timeline(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
):
    attempt = db.get(ExamAttempt, attempt_id)

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail="Attempt not found",
        )

    get_authorized_exam(db, user, attempt.exam_id)

    timeline = []

    answer_logs = db.query(AnswerLog).filter(AnswerLog.attempt_id == attempt_id).all()

    for answer in answer_logs:
        timeline.append(
            {
                "at": answer.saved_at,
                "type": "ANSWER_SAVED",
                "question_id": answer.question_id,
            }
        )

    events = db.query(ExamEvent).filter(ExamEvent.attempt_id == attempt_id).all()

    for event in events:
        timeline.append(
            {
                "at": event.occurred_at,
                "type": event.event_type,
                "actor_id": event.actor_id,
                "note": event.note,
            }
        )

    timeline.sort(key=lambda item: item["at"])

    return {
        "attempt_id": attempt_id,
        "timeline": timeline,
    }


# --- Member 5: Examiner security review queue ---

RISK_WEIGHTS = {
    "TAB_SWITCH": 10,
    "FULLSCREEN_EXIT": 15,
    "COPY_PASTE": 20,
}


@router.get("/exams/{exam_id}/review-queue")
def security_review_queue(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
):
    # Existing helper checks organization access.
    get_authorized_exam(db, user, exam_id)

    attempts = (
        db.query(ExamAttempt, SecurityUser)
        .join(
            SecurityUser,
            SecurityUser.id == ExamAttempt.candidate_id,
        )
        .filter(ExamAttempt.exam_id == exam_id)
        .all()
    )

    if not attempts:
        return {"items": [], "total": 0}

    ids = [attempt.id for attempt, _ in attempts]

    events = (
        db.query(ExamEvent)
        .filter(ExamEvent.attempt_id.in_(ids))
        .order_by(
            ExamEvent.occurred_at.asc(),
            ExamEvent.id.asc(),
        )
        .all()
    )

    grouped = defaultdict(list)

    for event in events:
        grouped[event.attempt_id].append(event)

    items = []

    for attempt, candidate in attempts:
        history = grouped[attempt.id]

        violations = [e for e in history if e.event_type in RISK_WEIGHTS]

        if not violations:
            continue

        # Illustrative review-priority score.
        risk_score = min(
            100,
            sum(RISK_WEIGHTS[e.event_type] for e in violations),
        )

        latest = violations[-1]

        if risk_score >= 60:
            risk_level = "HIGH"
        elif risk_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        items.append(
            {
                "attempt_id": attempt.id,
                "candidate_id": candidate.id,
                "candidate_name": candidate.full_name,
                "candidate_email": candidate.email,
                "status": attempt.status,
                "violation_count": len(violations),
                "risk_score": risk_score,
                "risk_level": risk_level,
                "latest_event": latest.event_type,
                "latest_event_at": latest.occurred_at,
                "review_required": attempt.status == "FROZEN",
            }
        )

    items.sort(
        key=lambda item: (
            item["review_required"],
            item["risk_score"],
            item["latest_event_at"],
        ),
        reverse=True,
    )

    return {
        "items": items,
        "total": len(items),
    }


# --- Examiner side: student marks for an exam ---


@router.get("/exams/{exam_id}/results")
def exam_student_results(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(staff_only),
):
    get_authorized_exam(db, user, exam_id)

    rows = (
        db.query(ExamAttempt, SecurityUser, Result)
        .join(SecurityUser, SecurityUser.id == ExamAttempt.candidate_id)
        .outerjoin(Result, Result.attempt_id == ExamAttempt.id)
        .filter(ExamAttempt.exam_id == exam_id)
        .order_by(SecurityUser.full_name.asc(), ExamAttempt.attempt_number.asc())
        .all()
    )

    items = []
    for attempt, candidate, result in rows:
        items.append(
            {
                "attempt_id": attempt.id,
                "candidate_id": candidate.id,
                "candidate_name": candidate.full_name,
                "candidate_email": candidate.email,
                "attempt_number": attempt.attempt_number,
                "status": attempt.status,
                "submitted_at": attempt.submitted_at,
                "obtained_marks": result.obtained_marks if result else None,
                "total_marks": result.total_marks if result else None,
                "percentage": result.percentage if result else None,
                "passed": result.passed if result else None,
            }
        )

    return {"items": items, "total": len(items)}
