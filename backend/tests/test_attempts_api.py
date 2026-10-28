"""The student endpoints over HTTP (Member 4): JSON shapes the frontend will rely on."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.attempts.routes import router as attempts_router
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.grading.routes import router as results_router

from tests.test_attempts_flow import db, world, _jsonb_for_sqlite  # noqa: F401  (reuse the fixtures)


@pytest.fixture()
def client(world):  # noqa: F811
    """A small app with only the student routers, logged in as the student.
    It does not depend on main.py, so this flow is tested on its own;
    test_student_routes_are_registered_in_main_app below checks main.py separately."""
    db = world["db"]
    api = FastAPI()
    api.include_router(attempts_router)
    api.include_router(results_router)

    def _db():
        yield db

    api.dependency_overrides[get_db] = _db
    api.dependency_overrides[get_current_user] = lambda: world["student"]
    return TestClient(api)


def test_student_routes_are_registered_in_main_app():
    """If this fails, the Member 4 lines are missing at the bottom of backend/app/main.py."""
    from app.main import app

    paths = {route.path for route in app.routes}
    for expected in ("/api/attempts/my-exams", "/api/attempts/start",
                     "/api/attempts/{attempt_id}/answers", "/api/attempts/{attempt_id}/submit",
                     "/api/results/{attempt_id}", "/api/results/mine"):
        assert expected in paths, (
            f"{expected} is not registered. Add app.include_router(attempts_router) and "
            "app.include_router(results_router) at the bottom of backend/app/main.py"
        )


def test_http_flow_from_dashboard_to_result(client, world):
    exam_id = str(world["exam"].id)

    response = client.get("/api/attempts/my-exams")
    assert response.status_code == 200, response.text
    mine = response.json()
    assert mine[0]["id"] == exam_id and mine[0]["can_start"] is True

    info = client.get(f"/api/attempts/exams/{exam_id}").json()
    assert info["question_count"] == 3 and info["duration_minutes"] == 30

    started = client.post("/api/attempts/start", json={"exam_id": exam_id})
    assert started.status_code == 201
    attempt = started.json()
    assert len(attempt["questions"]) == 3 and "correct" not in str(attempt)

    q = attempt["questions"][0]
    saved = client.post(f"/api/attempts/{attempt['attempt_id']}/answers",
                        json={"question_id": q["id"], "selected_option": "B"})
    assert saved.status_code == 200 and saved.json()["saved"] is True

    bad = client.post(f"/api/attempts/{attempt['attempt_id']}/answers", json={"question_id": q["id"], "selected_option": "Z"})
    assert bad.status_code == 422

    assert client.get(f"/api/results/{attempt['attempt_id']}").status_code == 409  # not submitted yet

    done = client.post(f"/api/attempts/{attempt['attempt_id']}/submit").json()
    assert done["status"] == "SUBMITTED"

    result = client.get(f"/api/results/{attempt['attempt_id']}").json()
    assert result["correct_count"] == 1 and result["total_marks"] == 3
    assert len(result["breakdown"]) == 3 and result["breakdown"][0]["question"]

    assert client.get("/api/results/mine").json()[0]["attempt_id"] == attempt["attempt_id"]
