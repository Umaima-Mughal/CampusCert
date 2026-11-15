"""AI paper generator (Groq). Runs on in-memory SQLite and a fake Groq: no network, no API key needed."""
import json

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai import groq_client
from app.ai.config import AISettings
from app.ai.groq_client import GroqError, chat_json
from app.ai.schemas import AIPaperRequest
from app.ai.service import build_ai_paper
from app.auth.models import Role, User
from app.core.database import Base, get_db
from app.organizations.models import Organization
from app.questions.access import bank_user
from app.questions.models import ExamPaperItem, Question


@compiles(JSONB, "sqlite")
def _jsonb_for_sqlite(element, compiler, **kw):
    return "JSON"


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    yield session
    session.close()


@pytest.fixture()
def examiner(db):
    org = Organization(name="Test Uni", slug="test-uni", org_code="CC-TEST01")
    role = Role(name="examiner")
    db.add_all([org, role])
    db.flush()
    user = User(full_name="Ex", email="e@test.edu", hashed_password="x", role_id=role.id, organization_id=org.id)
    db.add(user)
    db.commit()
    return user


def mcq(n, topic="Scheduling", diff="easy"):
    return {"topic": topic, "difficulty": diff, "question": f"Question number {n} about {topic}?",
            "option_a": f"A{n}", "option_b": f"B{n}", "option_c": f"C{n}", "option_d": f"D{n}",
            "correct_option": "ABCD"[n % 4], "solution": f"Because {n}."}


class FakeGroq:
    """Answers the plan call, then the question calls."""
    def __init__(self, plan=None, bad_every=0):
        self.plan = plan or {"title": "OS Midterm", "subject": "Operating Systems", "instructions": "Answer all.",
                             "duration_minutes": 20, "total_questions": 10,
                             "sections": [{"topic": "Scheduling", "difficulty": "easy", "count": 6},
                                          {"topic": "Memory", "difficulty": "hard", "count": 4}]}
        self.calls, self.counter, self.bad_every = [], 0, bad_every

    def __call__(self, messages, cfg=None, **kw):
        user = messages[-1]["content"]
        self.calls.append(user)
        if "Plan the paper" in user:
            return self.plan
        n_asked = int(user.split("Write ")[1].split(" ")[0])
        out = []
        for _ in range(n_asked):
            self.counter += 1
            q = mcq(self.counter)
            if self.bad_every and self.counter % self.bad_every == 0:
                q["option_b"] = q["option_a"]        # invalid: options not all different
            out.append(q)
        return {"questions": out}


def run(db, user, fake, **body):
    return build_ai_paper(db, user, AIPaperRequest(prompt="10 MCQs on operating systems", **body))


def test_prompt_becomes_saved_paper(db, examiner, monkeypatch):
    fake = FakeGroq()
    monkeypatch.setattr(groq_client, "chat_json", fake)
    paper, requested, skipped, warnings, _ = run(db, examiner, fake)
    assert (paper.title, requested, skipped, warnings) == ("OS Midterm", 10, 0, [])
    assert paper.duration_minutes == 20
    items = db.query(ExamPaperItem).filter_by(paper_id=paper.id).order_by(ExamPaperItem.position).all()
    assert len(items) == 10
    qs = db.query(Question).all()
    assert len(qs) == 10
    assert all(q.created_by == examiner.id and q.organization_id == examiner.organization_id for q in qs)
    assert all(q.correct_option in "ABCD" and q.option_d and q.solution for q in qs)
    assert {q.subject for q in qs} == {"Operating Systems"}
    assert len(fake.calls) == 3          # 1 plan + batches of 8 and 2


def test_bad_questions_are_dropped_and_topped_up(db, examiner, monkeypatch):
    fake = FakeGroq(bad_every=5)
    monkeypatch.setattr(groq_client, "chat_json", fake)
    paper, requested, skipped, warnings, _ = run(db, examiner, fake)
    assert len(paper.items) == 10 and skipped >= 1 and warnings == []


def test_question_count_title_and_marks_override(db, examiner, monkeypatch):
    fake = FakeGroq()
    monkeypatch.setattr(groq_client, "chat_json", fake)
    paper, requested, *_ = run(db, examiner, fake, question_count=5, title="My title", duration_minutes=45, marks_each=2)
    assert (paper.title, paper.duration_minutes, requested, len(paper.items)) == ("My title", 45, 5, 5)
    assert {i.marks for i in paper.items} == {2}


def test_cap_is_enforced(db, examiner, monkeypatch):
    fake = FakeGroq(plan={"subject": "X", "total_questions": 500, "sections": [{"topic": "T", "difficulty": "easy", "count": 500}]})
    monkeypatch.setattr(groq_client, "chat_json", fake)
    monkeypatch.setattr("app.ai.service.get_ai_settings", lambda: AISettings(GROQ_API_KEY="k", AI_MAX_QUESTIONS=12))
    paper, requested, *_ = run(db, examiner, fake)
    assert requested == 12 and len(paper.items) == 12


def test_reuses_question_already_in_the_examiners_bank(db, examiner, monkeypatch):
    fake = FakeGroq()
    monkeypatch.setattr(groq_client, "chat_json", fake)
    run(db, examiner, fake)
    fake.counter = 0                      # AI writes exactly the same questions again
    run(db, examiner, fake)
    assert db.query(Question).count() == 10      # no duplicates, no unique-constraint crash


def test_nothing_usable_raises(db, examiner, monkeypatch):
    monkeypatch.setattr(groq_client, "chat_json",
                        lambda m, c=None, **k: FakeGroq().plan if "Plan the paper" in m[-1]["content"] else {"questions": []})
    with pytest.raises(GroqError):
        run(db, examiner, None)
    assert db.query(Question).count() == 0


# ---------------------------------------------------------------- Groq client (fake HTTP)
def cfg(**kw):
    return AISettings(GROQ_API_KEY="gsk_test", **kw)


def reply(content, status=200, headers=None):
    body = {"choices": [{"message": {"content": content}}]} if status == 200 else {"error": {"message": "nope"}}
    return httpx.Response(status, json=body, headers=headers or {})


def test_client_missing_key_is_503():
    with pytest.raises(GroqError) as e:
        chat_json([{"role": "user", "content": "hi"}], AISettings(GROQ_API_KEY="", LLM_API_KEY=""))
    assert e.value.status == 503


def test_client_sends_json_mode_and_key_and_parses_fenced_json():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return reply('```json\n{"ok": true}\n```')

    out = chat_json([{"role": "user", "content": "hi"}], cfg(), transport=httpx.MockTransport(handler))
    assert out == {"ok": True}
    assert seen["auth"] == "Bearer gsk_test"
    assert seen["body"]["response_format"] == {"type": "json_object"}
    assert seen["body"]["model"] == "llama-3.3-70b-versatile"


def test_client_retries_on_rate_limit_then_succeeds():
    answers = iter([reply("", 429, {"retry-after": "1"}), reply('{"ok": 1}')])
    waits = []
    out = chat_json([{"role": "user", "content": "x"}], cfg(),
                    transport=httpx.MockTransport(lambda r: next(answers)), sleep=waits.append)
    assert out == {"ok": 1} and waits == [1.0]


def test_client_falls_back_to_second_model_when_first_is_refused():
    models = []

    def handler(request):
        m = json.loads(request.content)["model"]
        models.append(m)
        return reply("", 400) if m == "llama-3.3-70b-versatile" else reply('{"ok": 2}')

    assert chat_json([{"role": "user", "content": "x"}], cfg(), transport=httpx.MockTransport(handler)) == {"ok": 2}
    assert models == ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]


def test_client_bad_key_is_503_and_not_retried():
    calls = []

    def handler(request):
        calls.append(1)
        return reply("", 401)

    with pytest.raises(GroqError) as e:
        chat_json([{"role": "user", "content": "x"}], cfg(), transport=httpx.MockTransport(handler))
    assert e.value.status == 503 and len(calls) == 1


# ---------------------------------------------------------------- HTTP endpoint
def test_endpoint_creates_paper_and_checks_role(db, examiner, monkeypatch):
    from app.ai.routes import router
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[bank_user] = lambda: examiner
    monkeypatch.setattr(groq_client, "chat_json", FakeGroq())
    c = TestClient(app)

    r = c.post("/api/v1/ai/generate-paper", json={"prompt": "10 MCQs on operating systems"})
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["question_count"] == 10 and data["title"] == "OS Midterm" and data["requested"] == 10
    assert data["items"][0]["question"]["correct_option"] in "ABCD"

    assert c.post("/api/v1/ai/generate-paper", json={"prompt": "hi"}).status_code == 422   # too short

    def boom(*a, **k):
        raise GroqError("The free AI limit was reached.", 429)
    monkeypatch.setattr(groq_client, "chat_json", boom)
    assert c.post("/api/v1/ai/generate-paper", json={"prompt": "10 MCQs on operating systems"}).status_code == 429


def test_login_is_required():
    from app.ai.routes import router
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    # without a login token the route is closed (bank_user = examiner / super_admin only)
    r = TestClient(app).post("/api/v1/ai/generate-paper", json={"prompt": "10 MCQs on operating systems"})
    assert r.status_code in (401, 403)
