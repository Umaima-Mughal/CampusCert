"""Examiner side: student marks per exam (GET /api/analytics/exams/{id}/results)."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.analytics.routes import router as analytics_router
from app.attempts import services
from app.attempts.schemas import AnswerIn
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.database import get_db

from tests.test_attempts_flow import db, world, _jsonb_for_sqlite  # noqa: F401  (reuse the fixtures)


def make_client(world, user):
    api = FastAPI()
    api.include_router(analytics_router)

    def _db():
        yield world["db"]

    api.dependency_overrides[get_db] = _db
    api.dependency_overrides[get_current_user] = lambda: user
    return TestClient(api)


def admin_of(world):
    return world["db"].query(User).filter_by(email="a@x.edu").one()


def test_examiner_sees_student_marks(world):
    db, s, exam = world["db"], world["student"], world["exam"]
    attempt = services.start_attempt(db, s, exam.id)
    services.save_answer(db, s, attempt.id, AnswerIn(question_id=world["qids"][0], selected_option="B"))
    services.submit_attempt(db, s, attempt.id)

    response = make_client(world, admin_of(world)).get(f"/api/analytics/exams/{exam.id}/results")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    row = body["items"][0]
    assert row["candidate_name"] == "S"
    assert (row["obtained_marks"], row["total_marks"]) == (1, 3)
    assert row["passed"] is False


def test_in_progress_attempt_has_no_marks_yet(world):
    db, s, exam = world["db"], world["student"], world["exam"]
    services.start_attempt(db, s, exam.id)

    response = make_client(world, admin_of(world)).get(f"/api/analytics/exams/{exam.id}/results")
    row = response.json()["items"][0]
    assert row["status"] == "ACTIVE" and row["obtained_marks"] is None


def test_students_cannot_view_exam_marks_list(world):
    response = make_client(world, world["student"]).get(f"/api/analytics/exams/{world['exam'].id}/results")
    assert response.status_code == 403
