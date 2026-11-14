"""Rules for exams and their question papers: going live, taking an exam off air, removing a paper,
and deleting an exam. Runs on an in-memory SQLite database, so no Postgres is needed."""
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.models import Role, User
from app.core.base_model import BaseModel
from app.core.database import Base
from app.exams import services
from app.exams.constants import (
    STATUS_ACTIVE, STATUS_ARCHIVED, STATUS_CLOSED, STATUS_DRAFT, STATUS_SCHEDULED,
)
from app.exams.models import Exam
from app.exams.schemas import ExamUpdate
from app.organizations.models import Organization
from app.questions.models import ExamPaper, ExamPaperItem, Question, question_hash


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
def admin(db):
    org = Organization(name="Test Uni", slug="test-uni", org_code="CC-TEST01")
    role = Role(name="admin")
    db.add_all([org, role])
    db.flush()
    user = User(full_name="Admin", email="a@test.edu", hashed_password="x", role_id=role.id, organization_id=org.id)
    db.add(user)
    db.commit()
    return user


def make_paper(db, admin, n_questions):
    paper = ExamPaper(title=f"paper with {n_questions}", organization_id=admin.organization_id)
    db.add(paper)
    db.flush()
    for i in range(n_questions):
        q = Question(subject="S", difficulty="easy", topic="T", question=f"Q{i} of {paper.id}",
                     content_hash=question_hash("S", "T", f"Q{i} of {paper.id}"), organization_id=admin.organization_id)
        db.add(q)
        db.flush()
        db.add(ExamPaperItem(paper_id=paper.id, question_id=q.id, position=i + 1, marks=1))
    db.commit()
    return paper


def make_exam(db, admin, status=STATUS_DRAFT, paper=None, scheduled=False, distribution=None):
    start = datetime(2030, 1, 1, 9, 0) if scheduled else None
    exam = Exam(organization_id=admin.organization_id, created_by_user_id=admin.id, name="ned",
                duration_minutes=60, status=status, starts_at=start,
                ends_at=start + timedelta(hours=2) if start else None,
                max_students=10, paper_id=paper.id if paper else None, distribution=distribution or {})
    db.add(exam)
    db.commit()
    return exam


def refuses(fn, *args):
    with pytest.raises(HTTPException) as err:
        fn(*args)
    assert err.value.status_code == 400
    return err.value.detail


# ---------- the exam in the bug report: live, not scheduled, empty paper ----------
def test_live_exam_with_no_schedule_can_be_deactivated(db, admin):
    exam = make_exam(db, admin, STATUS_ACTIVE, make_paper(db, admin, 0))
    services.deactivate_exam(db, exam)
    assert exam.status == STATUS_DRAFT


def test_live_scheduled_exam_goes_back_to_scheduled(db, admin):
    exam = make_exam(db, admin, STATUS_ACTIVE, make_paper(db, admin, 2), scheduled=True)
    services.deactivate_exam(db, exam)
    assert exam.status == STATUS_SCHEDULED


# ---------- an empty paper must never go live ----------
def test_cannot_activate_with_empty_paper(db, admin):
    exam = make_exam(db, admin, STATUS_DRAFT, make_paper(db, admin, 0))
    assert "no questions" in refuses(services.change_exam_status, db, exam, STATUS_ACTIVE)
    assert exam.status == STATUS_DRAFT


def test_can_activate_with_questions(db, admin):
    exam = make_exam(db, admin, STATUS_DRAFT, make_paper(db, admin, 3))
    assert services.change_exam_status(db, exam, STATUS_ACTIVE).status == STATUS_ACTIVE


def test_distribution_only_exam_can_still_activate(db, admin):
    exam = make_exam(db, admin, STATUS_DRAFT, None, distribution={"subj": 5})
    assert services.change_exam_status(db, exam, STATUS_ACTIVE).status == STATUS_ACTIVE


# ---------- removing / swapping the paper of a live exam ----------
def test_empty_paper_can_be_removed_from_a_live_exam_and_exam_leaves_live_window(db, admin):
    exam = make_exam(db, admin, STATUS_ACTIVE, make_paper(db, admin, 0))
    services.update_exam(db, exam, ExamUpdate(paper_id=None))
    assert exam.paper_id is None and exam.status == STATUS_DRAFT


def test_empty_paper_can_be_swapped_for_one_with_questions_and_stays_live(db, admin):
    good = make_paper(db, admin, 2)
    exam = make_exam(db, admin, STATUS_ACTIVE, make_paper(db, admin, 0))
    services.update_exam(db, exam, ExamUpdate(paper_id=good.id))
    assert exam.paper_id == good.id and exam.status == STATUS_ACTIVE


def test_cannot_swap_empty_paper_for_another_empty_paper(db, admin):
    exam = make_exam(db, admin, STATUS_ACTIVE, make_paper(db, admin, 0))
    assert "no questions" in refuses(services.update_exam, db, exam, ExamUpdate(paper_id=make_paper(db, admin, 0).id))


def test_live_exam_with_questions_keeps_its_paper_but_says_how_to_change_it(db, admin):
    exam = make_exam(db, admin, STATUS_ACTIVE, make_paper(db, admin, 2))
    assert "Deactivate" in refuses(services.update_exam, db, exam, ExamUpdate(paper_id=None))


def test_paper_can_be_removed_from_a_draft(db, admin):
    exam = make_exam(db, admin, STATUS_DRAFT, make_paper(db, admin, 2))
    services.update_exam(db, exam, ExamUpdate(paper_id=None))
    assert exam.paper_id is None


# ---------- deleting an exam ----------
@pytest.mark.parametrize("status,questions,allowed", [
    (STATUS_DRAFT, 2, True), (STATUS_SCHEDULED, 2, True),
    (STATUS_ACTIVE, 0, True), (STATUS_CLOSED, 0, True), (STATUS_ARCHIVED, 0, True),
    (STATUS_ACTIVE, 2, False), (STATUS_CLOSED, 2, False), (STATUS_ARCHIVED, 2, False),
])
def test_delete_rules(db, admin, status, questions, allowed):
    exam = make_exam(db, admin, status, make_paper(db, admin, questions))
    exam_id = exam.id
    if allowed:
        services.delete_exam(db, exam)
        assert db.query(Exam).filter(Exam.id == exam_id).first() is None
    else:
        refuses(services.delete_exam, db, exam)
        assert db.query(Exam).filter(Exam.id == exam_id).first() is not None


def test_exam_with_no_paper_at_all_can_be_deleted_when_live(db, admin):
    services.delete_exam(db, make_exam(db, admin, STATUS_ACTIVE, None))


# ---------- flags the page uses to show or hide buttons ----------
def test_flags_for_the_live_empty_exam(db, admin):
    flags = services.exam_flags(db, make_exam(db, admin, STATUS_ACTIVE, make_paper(db, admin, 0)))
    assert flags == {"paper_question_count": 0, "can_delete": True, "can_change_paper": True}


def test_flags_for_a_live_exam_with_questions(db, admin):
    flags = services.exam_flags(db, make_exam(db, admin, STATUS_ACTIVE, make_paper(db, admin, 4)))
    assert flags == {"paper_question_count": 4, "can_delete": False, "can_change_paper": False}
