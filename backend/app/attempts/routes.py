"""
app/attempts/routes.py  (Member 4)

  GET  /api/attempts/my-exams                 student dashboard: my assigned exams
  GET  /api/attempts/exams/{exam_id}          instructions page
  POST /api/attempts/start                    start (or resume) an attempt
  GET  /api/attempts/{attempt_id}             the exam screen: questions, saved answers, time left
  POST /api/attempts/{attempt_id}/answers     autosave one answer
  POST /api/attempts/{attempt_id}/submit      finish and grade
"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.auth.models import User
from app.core.database import get_db
from app.exams.constants import STUDENT_ROLE

from . import services
from .schemas import AnswerIn, StartAttemptIn

router = APIRouter(prefix="/api/attempts", tags=["attempts"])

student_only = require_role(STUDENT_ROLE)


@router.get("/my-exams")
def my_exams(db: Session = Depends(get_db), user: User = Depends(student_only)):
    return services.list_my_exams(db, user)


@router.get("/exams/{exam_id}")
def exam_instructions(exam_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(student_only)):
    return services.exam_instructions(db, user, exam_id)


@router.post("/start", status_code=status.HTTP_201_CREATED)
def start(body: StartAttemptIn, db: Session = Depends(get_db), user: User = Depends(student_only)):
    attempt = services.start_attempt(db, user, body.exam_id)
    return services.attempt_view(db, user, attempt.id)


@router.get("/{attempt_id}")
def get_attempt(attempt_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(student_only)):
    return services.attempt_view(db, user, attempt_id)


@router.post("/{attempt_id}/answers")
def save_answer(attempt_id: uuid.UUID, body: AnswerIn, db: Session = Depends(get_db),
                user: User = Depends(student_only)):
    return services.save_answer(db, user, attempt_id, body)


@router.post("/{attempt_id}/submit")
def submit(attempt_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(student_only)):
    return services.submit_attempt(db, user, attempt_id)
