"""The demo-data script (scripts/seed_demo_data.py): adds the demo setup, is safe to repeat, removes it completely."""
import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.attempts import services
from app.attempts.models import ExamAttempt
from app.auth.models import Role, User
from app.core.database import Base
from app.exams.models import Exam
from app.grading.models import Result
from app.organizations.models import Organization
from app.questions.models import ExamPaper, Question


@compiles(JSONB, "sqlite")
def _jsonb_for_sqlite(element, compiler, **kw):
    return "JSON"


def load_seed_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "seed_demo_data.py"
    spec = importlib.util.spec_from_file_location("seed_demo_data", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def _foreign_keys_on(dbapi_connection, record):  # enforce foreign keys like Postgres does
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    session.add_all([Role(name=n) for n in ("student", "examiner", "admin", "super_admin")])
    session.commit()
    yield session
    session.close()


def counts(db):
    return {m.__name__: db.query(m).count() for m in (Organization, User, Exam, Question, ExamPaper)}


def test_seed_creates_the_demo_setup(db):
    seed = load_seed_module()
    seed.seed(db)
    assert counts(db) == {"Organization": 1, "User": 4, "Exam": 3, "Question": 10, "ExamPaper": 1}
    student = db.query(User).filter(User.email == seed.STUDENT_EMAILS[0]).one()
    assert student.role.name == "student"


def test_seed_twice_does_not_duplicate(db):
    seed = load_seed_module()
    seed.seed(db)
    first = counts(db)
    seed.seed(db)
    assert counts(db) == first


def test_demo_student_can_really_take_the_demo_exam(db):
    seed = load_seed_module()
    seed.seed(db)
    student = db.query(User).filter(User.email == seed.STUDENT_EMAILS[0]).one()
    quiz = next(e for e in services.list_my_exams(db, student) if e["name"] == seed.EXAM_NAMES[0])
    upcoming = next(e for e in services.list_my_exams(db, student) if e["name"] == seed.EXAM_NAMES[2])
    assert quiz["can_start"] is True and upcoming["can_start"] is False
    attempt = services.start_attempt(db, student, quiz["id"])
    assert len(attempt.layout["questions"]) == 10
    services.submit_attempt(db, student, attempt.id)
    assert db.query(Result).filter_by(attempt_id=attempt.id).one().unanswered_count == 10


def test_remove_deletes_everything_including_attempts_and_results(db):
    seed = load_seed_module()
    seed.seed(db)
    student = db.query(User).filter(User.email == seed.STUDENT_EMAILS[0]).one()
    exam = db.query(Exam).filter(Exam.name == seed.EXAM_NAMES[0]).one()
    attempt = services.start_attempt(db, student, exam.id)
    services.submit_attempt(db, student, attempt.id)

    seed.remove(db)
    assert counts(db) == {"Organization": 0, "User": 0, "Exam": 0, "Question": 0, "ExamPaper": 0}
    assert db.query(ExamAttempt).count() == 0 and db.query(Result).count() == 0
    seed.remove(db)  # a second remove is harmless
