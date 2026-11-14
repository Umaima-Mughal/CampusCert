"""
app/attempts/services.py  (Member 4)

The attempt lifecycle: start -> answer (autosave) -> submit -> grade.
Routes stay thin; every rule lives here so it can be unit tested without HTTP.
"""
import random
import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models import User
from app.exams.constants import STATUS_ACTIVE
from app.exams.models import Exam, ExamCandidate
from app.grading.grader import grade
from app.grading.models import Result
from app.questions.models import ExamPaperItem, Question

from .constants import (
    ATTEMPT_ACTIVE, ATTEMPT_SUBMITTED, FINISHED_STATUSES, OPEN_STATUSES, OPTION_KEYS,
)
from .models import AnswerLog, CandidateAnswer, ExamAttempt, utcnow
from .schemas import AnswerIn


def _now() -> datetime:
    return utcnow()  # the database stores naive UTC times


# ------------------------------------------------------------------ lookups
def _exam_for_student(db: Session, user: User, exam_id: uuid.UUID) -> Exam:
    """The exam, but only if this student has been assigned to it."""
    exam = (
        db.query(Exam)
        .join(ExamCandidate, ExamCandidate.exam_id == Exam.id)
        .filter(Exam.id == exam_id, ExamCandidate.user_id == user.id)
        .first()
    )
    if not exam:
        raise HTTPException(404, "Exam not found.")
    return exam


def _my_attempt(db: Session, user: User, attempt_id: uuid.UUID) -> ExamAttempt:
    attempt = (
        db.query(ExamAttempt)
        .filter(ExamAttempt.id == attempt_id, ExamAttempt.candidate_id == user.id)
        .first()
    )
    if not attempt:  # also what you get for someone else's attempt: never reveal that it exists
        raise HTTPException(404, "Attempt not found.")
    return attempt


def _remaining_seconds(attempt: ExamAttempt) -> int:
    if attempt.status not in OPEN_STATUSES:
        return 0
    return max(0, int((attempt.expires_at - _now()).total_seconds()))


# ------------------------------------------------------------------ rules
def start_block_reason(exam: Exam, used_attempts: int, now: datetime) -> str | None:
    """Why this student cannot START a new attempt right now (None = they can)."""
    if exam.status != STATUS_ACTIVE:
        return "This exam is not open."
    if exam.starts_at and now < exam.starts_at:
        return "This exam has not started yet."
    if exam.ends_at and now >= exam.ends_at:
        return "The exam window has closed."
    if used_attempts >= exam.max_attempts:
        return f"You have used all {exam.max_attempts} attempt(s) for this exam."
    if exam.paper_id is None:
        return "This exam has no question paper yet."
    return None


def _build_layout(db: Session, exam: Exam) -> dict:
    """Freeze this student's exam: which questions, in which order, with options in which order."""
    items = (
        db.query(ExamPaperItem)
        .filter(ExamPaperItem.paper_id == exam.paper_id)
        .order_by(ExamPaperItem.position)
        .all()
    )
    found = {q.id: q for q in db.query(Question).filter(Question.id.in_([i.question_id for i in items]))}

    questions = []
    for item in items:
        q = found.get(item.question_id)
        if q is None:
            continue
        letters = [k for k in OPTION_KEYS if (getattr(q, f"option_{k.lower()}") or "").strip()]
        if len(letters) < 2:  # an old question with no options cannot be answered
            continue
        random.shuffle(letters)
        questions.append({"id": q.id, "marks": item.marks, "correct": q.correct_option, "options": letters})

    if not questions:
        raise HTTPException(409, "The question paper of this exam has no answerable questions.")
    if exam.shuffle_questions:
        random.shuffle(questions)
    return {"questions": questions}


# ------------------------------------------------------------------ finishing
def finalize_attempt(db: Session, attempt: ExamAttempt, final_status: str = ATTEMPT_SUBMITTED,
                     when: datetime | None = None) -> Result:
    """
    Close an attempt and grade it. Safe to call twice (returns the existing result).
    Member 5 can call this with final_status="TERMINATED" when an examiner ends an attempt.
    """
    existing = db.query(Result).filter(Result.attempt_id == attempt.id).first()
    if attempt.status in FINISHED_STATUSES and existing:
        return existing

    exam = db.get(Exam, attempt.exam_id)
    answers = {
        a.question_id: a.selected_option
        for a in db.query(CandidateAnswer).filter(CandidateAnswer.attempt_id == attempt.id)
    }
    outcome = grade(attempt.layout["questions"], answers, exam.passing_score)

    attempt.status = final_status
    attempt.submitted_at = when or _now()
    result = Result(attempt_id=attempt.id, exam_id=attempt.exam_id, candidate_id=attempt.candidate_id, **outcome)
    db.add(result)
    try:
        db.commit()
    except IntegrityError:  # two submits at the same moment: the other one won, use its result
        db.rollback()
        return db.query(Result).filter(Result.attempt_id == attempt.id).first()
    db.refresh(result)
    return result


def finish_if_time_is_up(db: Session, attempt: ExamAttempt) -> bool:
    """If the clock ran out, submit and grade the attempt now. Returns True if it did."""
    if attempt.status in OPEN_STATUSES and _now() >= attempt.expires_at:
        finalize_attempt(db, attempt, ATTEMPT_SUBMITTED, when=attempt.expires_at)
        return True
    return False


# ------------------------------------------------------------------ dashboard
def list_my_exams(db: Session, user: User) -> list[dict]:
    exams = (
        db.query(Exam)
        .join(ExamCandidate, ExamCandidate.exam_id == Exam.id)
        .filter(ExamCandidate.user_id == user.id, Exam.status.in_(["SCHEDULED", "ACTIVE", "CLOSED"]))
        .order_by(Exam.starts_at.is_(None), Exam.starts_at)
        .all()
    )
    now = _now()
    out = []
    for exam in exams:
        attempts = (
            db.query(ExamAttempt)
            .filter(ExamAttempt.exam_id == exam.id, ExamAttempt.candidate_id == user.id)
            .order_by(ExamAttempt.attempt_number)
            .all()
        )
        for a in attempts:
            finish_if_time_is_up(db, a)
        open_attempt = next((a for a in attempts if a.status in OPEN_STATUSES), None)
        last = attempts[-1] if attempts else None
        reason = None if open_attempt else start_block_reason(exam, len(attempts), now)
        out.append({
            "id": exam.id, "name": exam.name, "description": exam.description,
            "duration_minutes": exam.duration_minutes, "status": exam.status,
            "starts_at": exam.starts_at, "ends_at": exam.ends_at,
            "max_attempts": exam.max_attempts, "attempts_used": len(attempts),
            "open_attempt_id": open_attempt.id if open_attempt else None,
            "last_attempt_id": last.id if last else None,
            "last_attempt_status": last.status if last else None,
            "can_start": open_attempt is not None or reason is None,
            "blocked_reason": reason,
        })
    return out


def exam_instructions(db: Session, user: User, exam_id: uuid.UUID) -> dict:
    exam = _exam_for_student(db, user, exam_id)
    count = 0
    if exam.paper_id:
        count = db.query(ExamPaperItem).filter(ExamPaperItem.paper_id == exam.paper_id).count()
    return {
        "id": exam.id, "name": exam.name, "description": exam.description,
        "instructions": exam.instructions, "duration_minutes": exam.duration_minutes,
        "question_count": count, "passing_score": exam.passing_score,
        "max_attempts": exam.max_attempts, "starts_at": exam.starts_at, "ends_at": exam.ends_at,
    }


# ------------------------------------------------------------------ start / read
def start_attempt(db: Session, user: User, exam_id: uuid.UUID) -> ExamAttempt:
    exam = _exam_for_student(db, user, exam_id)
    now = _now()

    attempts = (
        db.query(ExamAttempt)
        .filter(ExamAttempt.exam_id == exam.id, ExamAttempt.candidate_id == user.id)
        .all()
    )
    for a in attempts:
        finish_if_time_is_up(db, a)

    open_attempt = next((a for a in attempts if a.status in OPEN_STATUSES), None)
    if open_attempt:  # page refreshed or browser closed: carry on where they were
        return open_attempt

    reason = start_block_reason(exam, len(attempts), now)
    if reason:
        raise HTTPException(409, reason)

    expires_at = now + timedelta(minutes=exam.duration_minutes)
    if exam.ends_at and exam.ends_at < expires_at:
        expires_at = exam.ends_at  # nobody may sit past the end of the exam window

    attempt = ExamAttempt(
        exam_id=exam.id, candidate_id=user.id, attempt_number=len(attempts) + 1,
        status=ATTEMPT_ACTIVE, started_at=now, expires_at=expires_at,
        layout=_build_layout(db, exam),
    )
    db.add(attempt)
    try:
        db.commit()
    except IntegrityError:  # double click: the first request already created it
        db.rollback()
        again = (
            db.query(ExamAttempt)
            .filter(ExamAttempt.exam_id == exam.id, ExamAttempt.candidate_id == user.id,
                    ExamAttempt.status.in_(OPEN_STATUSES))
            .first()
        )
        if again:
            return again
        raise
    db.refresh(attempt)
    return attempt


def attempt_view(db: Session, user: User, attempt_id: uuid.UUID) -> dict:
    """Everything the exam screen needs. Never contains the correct answers."""
    attempt = _my_attempt(db, user, attempt_id)
    finish_if_time_is_up(db, attempt)
    exam = db.get(Exam, attempt.exam_id)

    questions = []
    if attempt.status in OPEN_STATUSES:
        layout = attempt.layout["questions"]
        texts = {q.id: q for q in db.query(Question).filter(Question.id.in_([q["id"] for q in layout]))}
        saved = {a.question_id: a for a in db.query(CandidateAnswer).filter(CandidateAnswer.attempt_id == attempt.id)}
        for position, item in enumerate(layout, start=1):
            q = texts[item["id"]]
            mine = saved.get(item["id"])
            questions.append({
                "id": q.id, "position": position, "text": q.question, "marks": item["marks"],
                "options": [{"key": k, "text": getattr(q, f"option_{k.lower()}")} for k in item["options"]],
                "selected": mine.selected_option if mine else None,
                "marked_for_review": bool(mine and mine.marked_for_review),
            })

    return {
        "attempt_id": attempt.id, "exam_id": exam.id, "exam_name": exam.name,
        "status": attempt.status, "started_at": attempt.started_at, "expires_at": attempt.expires_at,
        "remaining_seconds": _remaining_seconds(attempt), "server_time": _now(),
        "questions": questions,
    }


# ------------------------------------------------------------------ autosave / submit
def save_answer(db: Session, user: User, attempt_id: uuid.UUID, body: AnswerIn) -> dict:
    attempt = _my_attempt(db, user, attempt_id)
    if finish_if_time_is_up(db, attempt):
        raise HTTPException(409, "Time is up. Your exam was submitted automatically.")
    if attempt.status != ATTEMPT_ACTIVE:
        raise HTTPException(409, f"This attempt is {attempt.status}; answers cannot be saved now.")

    item = next((q for q in attempt.layout["questions"] if q["id"] == body.question_id), None)
    if item is None:
        raise HTTPException(404, "That question is not part of this exam.")
    if body.selected_option is not None and body.selected_option not in item["options"]:
        raise HTTPException(422, "That option does not exist for this question.")

    now = _now()
    row = (
        db.query(CandidateAnswer)
        .filter(CandidateAnswer.attempt_id == attempt.id, CandidateAnswer.question_id == body.question_id)
        .first()
    )
    if row is None:
        row = CandidateAnswer(attempt_id=attempt.id, question_id=body.question_id, marked_for_review=False)
        db.add(row)

    sent = body.model_fields_set  # tells "left out" apart from "explicitly null (clear it)"
    if "selected_option" in sent:
        row.selected_option = body.selected_option
        row.answered_at = now
    if "marked_for_review" in sent and body.marked_for_review is not None:
        row.marked_for_review = body.marked_for_review

    db.add(AnswerLog(attempt_id=attempt.id, question_id=body.question_id, saved_at=now,
                     selected_option=row.selected_option, marked_for_review=row.marked_for_review))
    db.commit()
    return {"saved": True, "saved_at": now, "remaining_seconds": _remaining_seconds(attempt)}


def submit_attempt(db: Session, user: User, attempt_id: uuid.UUID) -> dict:
    attempt = _my_attempt(db, user, attempt_id)
    if attempt.status in FINISHED_STATUSES:  # pressing Submit twice is harmless
        return {"attempt_id": attempt.id, "status": attempt.status}
    if attempt.status != ATTEMPT_ACTIVE:
        raise HTTPException(409, f"This attempt is {attempt.status}; it cannot be submitted now.")
    finalize_attempt(db, attempt, ATTEMPT_SUBMITTED)
    return {"attempt_id": attempt.id, "status": attempt.status}
