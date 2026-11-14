"""Attempt lifecycle (Member 4): start -> answer -> submit -> grade. In-memory SQLite, no Postgres."""
from datetime import datetime, timedelta

import uuid
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.attempts import services
from app.attempts.models import AnswerLog, ExamAttempt
from app.attempts.schemas import AnswerIn
from app.auth.models import Role, User
from app.core.database import Base
from app.exams.models import Exam, ExamCandidate
from app.grading.models import Result
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
def world(db):
    org = Organization(name="Uni", slug="uni", org_code="CC-1")
    student_role, admin_role = Role(name="student"), Role(name="admin")
    db.add_all([org, student_role, admin_role])
    db.flush()
    student = User(full_name="S", email="s@x.edu", hashed_password="x", role_id=student_role.id, organization_id=org.id)
    other = User(full_name="O", email="o@x.edu", hashed_password="x", role_id=student_role.id, organization_id=org.id)
    admin = User(full_name="A", email="a@x.edu", hashed_password="x", role_id=admin_role.id, organization_id=org.id)
    db.add_all([student, other, admin])
    db.flush()

    paper = ExamPaper(title="P", organization_id=org.id)
    db.add(paper)
    db.flush()
    qids = []
    for i in range(3):
        q = Question(subject="S", difficulty="easy", topic="T", question=f"Q{i}", content_hash=question_hash("S", "T", f"Q{i}"),
                     option_a="a", option_b="b", option_c="c", option_d="d", correct_option="B", organization_id=org.id)
        db.add(q)
        db.flush()
        db.add(ExamPaperItem(paper_id=paper.id, question_id=q.id, position=i + 1, marks=1))
        qids.append(q.id)

    exam = Exam(organization_id=org.id, created_by_user_id=admin.id, name="Exam", duration_minutes=30, status="ACTIVE",
                max_attempts=1, passing_score=50, paper_id=paper.id, shuffle_questions=True, distribution={})
    db.add(exam)
    db.flush()
    db.add(ExamCandidate(exam_id=exam.id, user_id=student.id))
    db.commit()
    return {"db": db, "org": org, "student": student, "other": other, "exam": exam, "qids": qids}


def err(fn, *args):
    with pytest.raises(HTTPException) as e:
        fn(*args)
    return e.value


def test_full_lifecycle_and_grade(db, world):
    s, exam = world["student"], world["exam"]
    attempt = services.start_attempt(db, s, exam.id)
    view = services.attempt_view(db, s, attempt.id)
    assert len(view["questions"]) == 3 and view["remaining_seconds"] > 1700
    assert "correct" not in str(view)  # the answers never reach the browser

    q1, q2, q3 = world["qids"]
    services.save_answer(db, s, attempt.id, AnswerIn(question_id=q1, selected_option="B"))
    services.save_answer(db, s, attempt.id, AnswerIn(question_id=q2, selected_option="A"))
    services.submit_attempt(db, s, attempt.id)

    result = db.query(Result).filter_by(attempt_id=attempt.id).one()
    assert (result.correct_count, result.incorrect_count, result.unanswered_count) == (1, 1, 1)
    assert result.passed is False  # 33% < 50%


def test_autosave_overwrites_answer_but_logs_every_save(db, world):
    s = world["student"]
    attempt = services.start_attempt(db, s, world["exam"].id)
    q = world["qids"][0]
    services.save_answer(db, s, attempt.id, AnswerIn(question_id=q, selected_option="A"))
    services.save_answer(db, s, attempt.id, AnswerIn(question_id=q, selected_option="C"))
    view = services.attempt_view(db, s, attempt.id)
    assert next(x for x in view["questions"] if x["id"] == q)["selected"] == "C"
    assert db.query(AnswerLog).filter_by(attempt_id=attempt.id).count() == 2


def test_mark_for_review_keeps_the_answer_and_null_clears_it(db, world):
    s = world["student"]
    attempt = services.start_attempt(db, s, world["exam"].id)
    q = world["qids"][0]
    services.save_answer(db, s, attempt.id, AnswerIn(question_id=q, selected_option="A"))
    services.save_answer(db, s, attempt.id, AnswerIn(question_id=q, marked_for_review=True))
    item = next(x for x in services.attempt_view(db, s, attempt.id)["questions"] if x["id"] == q)
    assert item["selected"] == "A" and item["marked_for_review"] is True
    services.save_answer(db, s, attempt.id, AnswerIn(question_id=q, selected_option=None))
    item = next(x for x in services.attempt_view(db, s, attempt.id)["questions"] if x["id"] == q)
    assert item["selected"] is None


def test_starting_twice_resumes_the_same_attempt(db, world):
    s, exam = world["student"], world["exam"]
    a1 = services.start_attempt(db, s, exam.id)
    a2 = services.start_attempt(db, s, exam.id)
    assert a1.id == a2.id


def test_attempt_limit(db, world):
    s, exam = world["student"], world["exam"]
    a = services.start_attempt(db, s, exam.id)
    services.submit_attempt(db, s, a.id)
    assert err(services.start_attempt, db, s, exam.id).status_code == 409


def test_only_assigned_students_can_start(db, world):
    assert err(services.start_attempt, db, world["other"], world["exam"].id).status_code == 404


def test_exam_must_be_active_and_in_its_window(db, world):
    s, exam = world["student"], world["exam"]
    exam.status = "SCHEDULED"
    db.commit()
    assert err(services.start_attempt, db, s, exam.id).status_code == 409
    exam.status = "ACTIVE"
    exam.starts_at = datetime.utcnow() + timedelta(hours=1)
    exam.ends_at = datetime.utcnow() + timedelta(hours=3)
    db.commit()
    assert "not started" in err(services.start_attempt, db, s, exam.id).detail
    exam.starts_at = datetime.utcnow() - timedelta(hours=3)
    exam.ends_at = datetime.utcnow() - timedelta(hours=1)
    db.commit()
    assert "closed" in err(services.start_attempt, db, s, exam.id).detail


def test_cannot_read_or_answer_someone_elses_attempt(db, world):
    attempt = services.start_attempt(db, world["student"], world["exam"].id)
    assert err(services.attempt_view, db, world["other"], attempt.id).status_code == 404
    assert err(services.save_answer, db, world["other"], attempt.id,
               AnswerIn(question_id=world["qids"][0], selected_option="A")).status_code == 404


def test_invalid_question_or_option_is_rejected(db, world):
    s = world["student"]
    attempt = services.start_attempt(db, s, world["exam"].id)
    assert err(services.save_answer, db, s, attempt.id, AnswerIn(question_id=99999, selected_option="A")).status_code == 404


def test_time_up_submits_and_grades_automatically(db, world):
    s = world["student"]
    attempt = services.start_attempt(db, s, world["exam"].id)
    services.save_answer(db, s, attempt.id, AnswerIn(question_id=world["qids"][0], selected_option="B"))
    attempt.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()
    assert err(services.save_answer, db, s, attempt.id,
               AnswerIn(question_id=world["qids"][1], selected_option="B")).status_code == 409
    db.refresh(attempt)
    assert attempt.status == "SUBMITTED"
    assert db.query(Result).filter_by(attempt_id=attempt.id).one().correct_count == 1


def test_frozen_attempt_rejects_answers(db, world):
    s = world["student"]
    attempt = services.start_attempt(db, s, world["exam"].id)
    attempt.status = "FROZEN"  # what Member 5 will do
    db.commit()
    assert err(services.save_answer, db, s, attempt.id,
               AnswerIn(question_id=world["qids"][0], selected_option="A")).status_code == 409


def test_submit_twice_is_harmless(db, world):
    s = world["student"]
    attempt = services.start_attempt(db, s, world["exam"].id)
    services.submit_attempt(db, s, attempt.id)
    services.submit_attempt(db, s, attempt.id)
    assert db.query(Result).filter_by(attempt_id=attempt.id).count() == 1


def test_attempt_keeps_its_questions_even_if_the_bank_changes(db, world):
    s = world["student"]
    attempt = services.start_attempt(db, s, world["exam"].id)
    q = db.get(Question, world["qids"][0])
    q.correct_option = "D"  # examiner edits the question mid-exam
    db.commit()
    services.save_answer(db, s, attempt.id, AnswerIn(question_id=q.id, selected_option="B"))
    services.submit_attempt(db, s, attempt.id)
    assert db.query(Result).filter_by(attempt_id=attempt.id).one().correct_count == 1  # graded on the snapshot


def test_my_exams_lists_only_assigned_exams_with_start_flag(db, world):
    rows = services.list_my_exams(db, world["student"])
    assert len(rows) == 1 and rows[0]["can_start"] is True
    assert services.list_my_exams(db, world["other"]) == []


# --- Member 5: Security workflow integration tests ---

from app.security.models import ExamEvent
from app.security.routes import (
    EventIn,
    ActionIn,
    record_integrity_event,
    resume_attempt,
    terminate_attempt,
)


def test_security_freeze_resume_terminate(db, world):
    student = world["student"]
    admin = db.query(User).filter(
        User.email == "a@x.edu"
    ).one()

    attempt = services.start_attempt(
        db, student, world["exam"].id
    )

    # 1. Student exits fullscreen
    response = record_integrity_event(
        EventIn(
            attempt_id=attempt.id,
            type="FULLSCREEN_EXIT",
        ),
        db=db,
        user=student,
    )

    assert response["frozen"] is True
    db.refresh(attempt)
    assert attempt.status == "FROZEN"

    # 2. Examiner resumes the attempt
    resume_attempt(
        attempt.id,
        ActionIn(reason="Reviewed incident"),
        db=db,
        user=admin,
    )

    db.refresh(attempt)
    assert attempt.status == "ACTIVE"

    # 3. Examiner terminates and grades
    terminate_attempt(
        attempt.id,
        ActionIn(reason="Examiner decision"),
        db=db,
        user=admin,
    )

    db.refresh(attempt)
    assert attempt.status == "TERMINATED"

    # 4. Result must exist
    result = db.query(Result).filter_by(
        attempt_id=attempt.id
    ).one_or_none()

    assert result is not None

    # 5. Audit records must be saved
    events = db.query(ExamEvent).filter_by(
        attempt_id=attempt.id
    ).all()

    event_types = [e.event_type for e in events]

    assert "FULLSCREEN_EXIT" in event_types
    assert "FROZEN" in event_types
    assert "RESUMED" in event_types
    assert "TERMINATED" in event_types


def test_student_cannot_record_other_attempt(db, world):
    student = world["student"]
    other = world["other"]

    attempt = services.start_attempt(
        db, student, world["exam"].id
    )

    with pytest.raises(HTTPException) as exc:
        record_integrity_event(
            EventIn(
                attempt_id=attempt.id,
                type="TAB_SWITCH",
            ),
            db=db,
            user=other,
        )

    assert exc.value.status_code == 404

    assert db.query(ExamEvent).filter_by(
        attempt_id=attempt.id
    ).count() == 0


def test_frozen_exam_rejects_answer_submission(db, world):
    student = world["student"]

    attempt = services.start_attempt(
        db, student, world["exam"].id
    )

    record_integrity_event(
        EventIn(
            attempt_id=attempt.id,
            type="FULLSCREEN_EXIT",
        ),
        db=db,
        user=student,
    )

    db.refresh(attempt)
    assert attempt.status == "FROZEN"

    question_id = world["qids"][0]

    with pytest.raises(HTTPException) as exc:
        services.save_answer(
            db,
            student,
            attempt.id,
            AnswerIn(
                question_id=question_id,
                selected_option="A",
            ),
        )

    assert exc.value.status_code == 409

    assert db.query(AnswerLog).filter_by(
        attempt_id=attempt.id
    ).count() == 0


def test_examiner_cannot_access_other_organization(
    db, world
):
    student = world["student"]

    attempt = services.start_attempt(
        db, student, world["exam"].id
    )

    class FakeRole:
        name = "examiner"

    class FakeExaminer:
        role = FakeRole()
        organization_id = uuid.UUID("00000000-0000-0000-0000-000000000999")

    from app.security.routes import get_staff_attempt

    with pytest.raises(HTTPException) as exc:
        get_staff_attempt(
            db,
            FakeExaminer(),
            attempt.id,
        )

    assert exc.value.status_code == 404

def test_duplicate_integrity_event_is_suppressed(db, world):
    student = world["student"]

    attempt = services.start_attempt(
        db, student, world["exam"].id
    )

    payload = EventIn(
        attempt_id=attempt.id,
        type="TAB_SWITCH",
    )

    first = record_integrity_event(
        payload, db=db, user=student
    )

    second = record_integrity_event(
        payload, db=db, user=student
    )

    assert first["recorded"] is True
    assert second["recorded"] is False
    assert second["duplicate"] is True

    count = db.query(ExamEvent).filter(
        ExamEvent.attempt_id == attempt.id,
        ExamEvent.event_type == "TAB_SWITCH",
    ).count()

    assert count == 1
