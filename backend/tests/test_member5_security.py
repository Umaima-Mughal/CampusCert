
"""Member 5: Basic security authorization tests."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from app.main import app


client = TestClient(app)

TEST_ID = "00000000-0000-0000-0000-000000000001"


def test_events_require_login():
    response = client.post(
        "/api/events",
        json={
            "attempt_id": TEST_ID,
            "type": "TAB_SWITCH"
        }
    )
    assert response.status_code in (401, 403)


def test_resume_requires_login():
    response = client.post(
        f"/api/attempts/{TEST_ID}/resume"
    )
    assert response.status_code in (401, 403)


def test_terminate_requires_login():
    response = client.post(
        f"/api/attempts/{TEST_ID}/terminate"
    )
    assert response.status_code in (401, 403)


def test_analytics_requires_login():
    response = client.get(
        f"/api/analytics/exams/{TEST_ID}/overview"
    )
    assert response.status_code in (401, 403)


def test_timeline_requires_login():
    response = client.get(
        f"/api/analytics/attempts/{TEST_ID}/timeline"
    )
    assert response.status_code in (401, 403)


from app.auth.dependencies import require_role
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient


def test_student_cannot_use_examiner_role():
    test_app = FastAPI()

    @test_app.get("/examiner-only")
    def examiner_only(
        user=Depends(
            require_role(
                "examiner",
                "admin",
                "super_admin",
            )
        )
    ):
        return {"allowed": True}

    test_client = TestClient(test_app)

    response = test_client.get("/examiner-only")

    assert response.status_code in (401, 403)


# --- Member 5: Authenticated role protection tests ---

from app.auth.dependencies import get_current_user
from app.security.routes import staff_only, student_only


def test_authenticated_student_cannot_use_examiner_actions():
    test_app = FastAPI()

    class FakeRole:
        name = "student"

    class FakeStudent:
        role = FakeRole()

    @test_app.post("/resume")
    def resume(
        user=Depends(staff_only)
    ):
        return {"allowed": True}

    @test_app.post("/terminate")
    def terminate(
        user=Depends(staff_only)
    ):
        return {"allowed": True}

    test_app.dependency_overrides[get_current_user] = (
        lambda: FakeStudent()
    )

    try:
        test_client = TestClient(test_app)

        resume_response = test_client.post("/resume")
        terminate_response = test_client.post("/terminate")

        assert resume_response.status_code == 403
        assert terminate_response.status_code == 403
    finally:
        test_app.dependency_overrides.clear()


def test_examiner_cannot_submit_student_integrity_event():
    test_app = FastAPI()

    class FakeRole:
        name = "examiner"

    class FakeExaminer:
        role = FakeRole()

    @test_app.post("/events")
    def events(
        user=Depends(student_only)
    ):
        return {"allowed": True}

    test_app.dependency_overrides[get_current_user] = (
        lambda: FakeExaminer()
    )

    try:
        response = TestClient(test_app).post("/events")
        assert response.status_code == 403
    finally:
        test_app.dependency_overrides.clear()
