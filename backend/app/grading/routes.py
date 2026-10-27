"""
app/grading/routes.py  (Member 4)

  GET /api/results/mine               my finished attempts with their scores
  GET /api/results/{attempt_id}       one result with the per-question breakdown
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.attempts import services as attempt_services
from app.attempts.constants import FINISHED_STATUSES, SHOW_CORRECT_ANSWERS
from app.attempts.models import ExamAttempt
from app.auth.dependencies import get_current_user, require_role
from app.auth.models import User
from app.core.database import get_db
from app.exams.constants import STUDENT_ROLE
from app.exams.models import Exam
from app.questions.models import Question

from .models import Result

router = APIRouter(prefix="/api/results", tags=["results"])

STAFF_ROLES = ("admin", "super_admin", "examiner")


def _summary(result: Result, exam_name: str, attempt: ExamAttempt) -> dict:
    return {
        "attempt_id": result.attempt_id, "exam_id": result.exam_id, "exam_name": exam_name,
        "attempt_number": attempt.attempt_number, "status": attempt.status,
        "submitted_at": attempt.submitted_at,
        "total_marks": result.total_marks, "obtained_marks": result.obtained_marks,
        "correct_count": result.correct_count, "incorrect_count": result.incorrect_count,
        "unanswered_count": result.unanswered_count,
        "percentage": result.percentage, "passed": result.passed,
    }


@router.get("/mine")
def my_results(db: Session = Depends(get_db), user: User = Depends(require_role(STUDENT_ROLE))):
    rows = (
        db.query(Result, ExamAttempt, Exam)
        .join(ExamAttempt, ExamAttempt.id == Result.attempt_id)
        .join(Exam, Exam.id == Result.exam_id)
        .filter(Result.candidate_id == user.id)
        .order_by(ExamAttempt.submitted_at.desc())
        .all()
    )
    return [_summary(r, e.name, a) for r, a, e in rows]


@router.get("/{attempt_id}")
def get_result(attempt_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    exam = db.get(Exam, attempt.exam_id) if attempt else None
    role = user.role.name

    allowed = False
    if attempt:
        if role == STUDENT_ROLE:
            allowed = attempt.candidate_id == user.id
        elif role == "super_admin":
            allowed = True
        elif role in STAFF_ROLES:
            allowed = exam.organization_id == user.organization_id
    if not allowed:
        raise HTTPException(404, "Result not found.")

    attempt_services.finish_if_time_is_up(db, attempt)  # a student who closed the tab still gets graded
    result = db.query(Result).filter(Result.attempt_id == attempt.id).first()
    if attempt.status not in FINISHED_STATUSES or result is None:
        raise HTTPException(409, "This attempt has not been submitted yet.")

    texts = {q.id: q for q in db.query(Question).filter(Question.id.in_([b["question_id"] for b in result.breakdown]))}
    hide_answers = role == STUDENT_ROLE and not SHOW_CORRECT_ANSWERS
    breakdown = []
    for b in result.breakdown:
        q = texts.get(b["question_id"])
        row = dict(b)
        row["question"] = q.question if q else None
        row["options"] = {k: getattr(q, f"option_{k.lower()}") for k in "ABCD" if q and getattr(q, f"option_{k.lower()}")}
        if hide_answers:
            row["correct"] = None
        breakdown.append(row)

    out = _summary(result, exam.name, attempt)
    out["passing_score"] = exam.passing_score
    out["breakdown"] = breakdown
    return out
