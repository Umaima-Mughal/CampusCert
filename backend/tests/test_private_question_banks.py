"""Private question banks: each examiner has their own; papers are shared inside an organization.
Uses an in-memory SQLite database, so no Postgres is needed."""
import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.questions import papers as papers_module
from app.questions import router as questions_module
from app.questions.access import bank_user, paper_reader
from app.questions.models import ExamPaper, ExamPaperItem, Question, question_hash

Q = "/api/v1/questions"
ORG_1, ORG_2 = uuid.uuid4(), uuid.uuid4()
CSV = (
    "Subject,Difficulty,Topic,Question,Option A,Option B,Option C,Option D,Correct Answer,Solution\n"
    "Physics,Easy,Motion,What is velocity?,Speed,Displacement per unit time,Mass,Force,B,"
    "Velocity is displacement divided by time.\n"
)


def make_user(role, org=ORG_1):
    return SimpleNamespace(id=uuid.uuid4(), organization_id=org, role=SimpleNamespace(name=role))


@pytest.fixture()
def env(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[Question.__table__, ExamPaper.__table__, ExamPaperItem.__table__])
    Session = sessionmaker(bind=engine)
    who = {}                                    # the user "logged in" for the next request

    def get_session():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = get_session
    app.dependency_overrides[bank_user] = lambda: who["user"]
    app.dependency_overrides[paper_reader] = lambda: who["user"]
    # no exams table in these tests: nothing is attached to an exam here
    monkeypatch.setattr(papers_module, "_guard_in_use", lambda *a, **k: None)
    monkeypatch.setattr(questions_module, "_refuse_if_locked", lambda *a, **k: None)
    yield SimpleNamespace(client=TestClient(app), Session=Session, who=who)
    for dep in (get_db, bank_user, paper_reader):
        app.dependency_overrides.pop(dep, None)


def call(env, user, method, url, **kwargs):
    env.who["user"] = user
    return env.client.request(method, url, **kwargs)


def add_question(env, owner, text, org=ORG_1):
    with env.Session() as db:
        q = Question(subject="Physics", difficulty="easy", topic="Motion", question=text,
                     option_a="a", option_b="b", option_c="c", option_d="d", correct_option="B",
                     solution="because", content_hash=question_hash("Physics", "Motion", text),
                     organization_id=org, created_by=owner.id)
        db.add(q)
        db.commit()
        return q.id


def make_paper(env, owner, question_ids, title="Paper"):
    items = [{"question_id": i, "marks": 1} for i in question_ids]
    r = call(env, owner, "POST", f"{Q}/papers", json={"title": title, "items": items})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_each_examiner_sees_only_their_own_questions(env):
    sultan, murtaza, outsider = make_user("examiner"), make_user("examiner"), make_user("examiner", ORG_2)
    add_question(env, sultan, "S1")
    add_question(env, sultan, "S2")
    add_question(env, murtaza, "M1")
    assert call(env, sultan, "GET", Q).json()["total"] == 2
    assert call(env, murtaza, "GET", Q).json()["total"] == 1
    assert call(env, outsider, "GET", Q).json()["total"] == 0


def test_an_examiner_cannot_put_someone_elses_question_in_a_new_paper(env):
    sultan, murtaza = make_user("examiner"), make_user("examiner")
    s1 = add_question(env, sultan, "S1")
    items = [{"question_id": s1, "marks": 1}]
    r = call(env, murtaza, "POST", f"{Q}/papers", json={"title": "Sneaky", "items": items})
    assert r.status_code == 422


def test_examiners_of_one_organization_share_papers_other_organizations_do_not(env):
    sultan, murtaza, outsider = make_user("examiner"), make_user("examiner"), make_user("examiner", ORG_2)
    paper_id = make_paper(env, sultan, [add_question(env, sultan, "S1")])
    assert len(call(env, murtaza, "GET", f"{Q}/papers").json()) == 1
    assert call(env, murtaza, "GET", f"{Q}/papers/{paper_id}").status_code == 200
    assert call(env, outsider, "GET", f"{Q}/papers").json() == []
    assert call(env, outsider, "GET", f"{Q}/papers/{paper_id}").status_code == 404


def test_another_examiner_can_edit_a_shared_paper(env):
    sultan, murtaza = make_user("examiner"), make_user("examiner")
    s1, s2 = add_question(env, sultan, "S1"), add_question(env, sultan, "S2")
    m1 = add_question(env, murtaza, "M1")
    paper_id = make_paper(env, sultan, [s1, s2])

    edit = {"title": "Edited by Murtaza", "items": [{"question_id": q, "marks": 2} for q in (s1, s2, m1)]}
    r = call(env, murtaza, "PUT", f"{Q}/papers/{paper_id}", json=edit)
    assert r.status_code == 200, r.text
    assert r.json()["title"] == "Edited by Murtaza" and r.json()["question_count"] == 3

    # ...but he still cannot pull in a question of Sultan's that is not already in the paper
    s3 = add_question(env, sultan, "S3")
    edit["items"].append({"question_id": s3, "marks": 1})
    assert call(env, murtaza, "PUT", f"{Q}/papers/{paper_id}", json=edit).status_code == 422


def test_admin_sees_every_paper_of_the_organization_without_answers(env):
    sultan, murtaza, admin = make_user("examiner"), make_user("examiner"), make_user("admin")
    paper_id = make_paper(env, sultan, [add_question(env, sultan, "S1")])
    make_paper(env, murtaza, [add_question(env, murtaza, "M1")])

    assert len(call(env, admin, "GET", f"{Q}/papers").json()) == 2
    seen_by_admin = call(env, admin, "GET", f"{Q}/papers/{paper_id}").json()["items"][0]["question"]
    assert seen_by_admin["correct_option"] is None and seen_by_admin["solution"] is None
    seen_by_examiner = call(env, murtaza, "GET", f"{Q}/papers/{paper_id}").json()["items"][0]["question"]
    assert seen_by_examiner["correct_option"] == "B"


def test_bulk_delete_cannot_touch_another_examiners_questions(env):
    sultan, murtaza = make_user("examiner"), make_user("examiner")
    s1 = add_question(env, sultan, "S1")
    paper_id = make_paper(env, sultan, [s1])
    r = call(env, murtaza, "POST", f"{Q}/bulk-delete", json={"ids": [s1]})
    assert r.status_code == 200 and r.json()["deleted"] == 0
    assert call(env, sultan, "GET", f"{Q}/papers/{paper_id}").json()["question_count"] == 1


def test_duplicates_are_checked_per_examiner(env):
    sultan, murtaza = make_user("examiner"), make_user("examiner")

    def upload(user):
        files = {"file": ("q.csv", CSV.encode(), "text/csv")}
        r = call(env, user, "POST", f"{Q}/import", files=files)
        assert r.status_code == 200, r.text
        return r.json()

    assert upload(sultan)["imported"] == 1
    assert upload(murtaza)["imported"] == 1          # his own copy, not a duplicate
    again = upload(sultan)
    assert again["imported"] == 0 and again["duplicates"] == 1
