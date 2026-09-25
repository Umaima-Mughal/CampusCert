from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.exams.constants import STATUS_ACTIVE, STATUS_DRAFT, STATUS_SCHEDULED
from app.exams.schemas import ExamCreate
from app.exams.services import can_transition
from app.main import app


def test_health_still_ok():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_exams_require_auth():
    client = TestClient(app)
    response = client.get("/api/exams")
    assert response.status_code in (401, 403)


def test_exam_create_schema_accepts_distribution():
    payload = ExamCreate(
        name="Midterm",
        duration_minutes=90,
        distribution={"subject-a": 5, "subject-b": 3},
    )
    assert payload.distribution["subject-a"] == 5


def test_exam_create_schema_rejects_zero_count():
    with pytest.raises(ValidationError):
        ExamCreate(name="Midterm", duration_minutes=60, distribution={"subject-a": 0})


def test_lifecycle_transitions():
    assert can_transition(STATUS_DRAFT, STATUS_SCHEDULED)
    assert can_transition(STATUS_SCHEDULED, STATUS_ACTIVE)
    assert can_transition(STATUS_ACTIVE, STATUS_SCHEDULED)
    assert not can_transition(STATUS_ACTIVE, STATUS_DRAFT)


def test_exam_window_helper_values():
    start = datetime(2026, 9, 24, 9, 0, 0)
    end = start + timedelta(hours=2)
    payload = ExamCreate(
        name="Windowed exam",
        duration_minutes=90,
        starts_at=start,
        ends_at=end,
    )
    assert payload.ends_at > payload.starts_at
