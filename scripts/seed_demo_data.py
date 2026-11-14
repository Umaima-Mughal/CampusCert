"""
scripts/seed_demo_data.py

Creates a small, clearly-labelled DEMO setup so you can try the whole student portal
without building an exam by hand:

  - organization "CampusCert Demo University"
  - users (password for all: Demo@12345)
        demo.admin@campuscert-demo.edu      admin
        demo.examiner@campuscert-demo.edu   examiner
        demo.student1@campuscert-demo.edu   student
        demo.student2@campuscert-demo.edu   student
  - 10 multiple-choice networking questions and one paper that uses them
  - 3 exams, with both students assigned:
        [DEMO] Computer Networks Quiz     ACTIVE, 15 minutes, 3 attempts
        [DEMO] 1-minute timer test        ACTIVE, 1 minute (to watch auto-submit and auto-grading)
        [DEMO] Upcoming exam              SCHEDULED, opens tomorrow (shows the "not open yet" state)

It only ADDS rows, it is safe to run twice, and `--remove` deletes exactly what it created.
IMPORTANT: it writes to the database named in backend\\.env. If that is the team's shared
Supabase database, the demo rows are visible to everyone until you run --remove.

Run from the backend folder with the virtual environment active:

    cd backend
    python ..\\scripts\\seed_demo_data.py            add the demo data
    python ..\\scripts\\seed_demo_data.py --remove   delete the demo data again
"""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy.engine import make_url  # noqa: E402

ORG_SLUG = "campuscert-demo"
ORG_CODE = "CC-DEMO01"
PASSWORD = "Demo@12345"
DOMAIN = "campuscert-demo.edu"  # a real-looking domain: the login form rejects reserved ones like .test
USERS = [
    ("Demo Admin", f"demo.admin@{DOMAIN}", "admin"),
    ("Demo Examiner", f"demo.examiner@{DOMAIN}", "examiner"),
    ("Demo Student One", f"demo.student1@{DOMAIN}", "student"),
    ("Demo Student Two", f"demo.student2@{DOMAIN}", "student"),
]
STUDENT_EMAILS = [f"demo.student1@{DOMAIN}", f"demo.student2@{DOMAIN}"]
SUBJECT = "Computer Networks (DEMO)"
TOPIC = "Basics"
PAPER_TITLE = "[DEMO] Computer Networks paper"
EXAM_NAMES = ["[DEMO] Computer Networks Quiz", "[DEMO] 1-minute timer test", "[DEMO] Upcoming exam"]

# (question, A, B, C, D, correct letter)
QUESTIONS = [
    ("Which layer of the OSI model is responsible for routing packets between networks?", "Physical", "Data link", "Network", "Transport", "C"),
    ("What is the default port number of HTTP?", "21", "25", "53", "80", "D"),
    ("Which transport protocol is connectionless?", "UDP", "TCP", "FTP", "SMTP", "A"),
    ("How many bits long is an IPv4 address?", "16", "32", "64", "128", "B"),
    ("Which device forwards packets between different networks?", "Hub", "Repeater", "Switch", "Router", "D"),
    ("What does DNS do?", "Encrypts web traffic", "Assigns IP addresses automatically", "Translates domain names to IP addresses", "Blocks unwanted traffic", "C"),
    ("In which topology is every device connected to a central device?", "Star", "Bus", "Ring", "Mesh", "A"),
    ("Which protocol is used to send web pages securely?", "HTTP", "HTTPS", "FTP", "Telnet", "B"),
    ("What does ARP map?", "Domain names to IP addresses", "Ports to services", "IP addresses to MAC addresses", "MAC addresses to ports", "C"),
    ("Which protocol automatically assigns IP addresses to devices?", "DHCP", "DNS", "ICMP", "SNMP", "A"),
]

INSTRUCTIONS = (
    "This is a DEMO exam created by scripts/seed_demo_data.py.\n"
    "Answer all questions. Each question has exactly one correct option.\n"
    "Your answers are saved automatically."
)


def confirm(db_url: str) -> None:
    url = make_url(db_url)
    print(f"Database: {url.drivername} on {url.host or 'local file'} / {url.database}")
    if input("Type YES to continue: ").strip() != "YES":
        print("Cancelled. Nothing was changed.")
        sys.exit(0)


def seed(db) -> None:
    from app.auth.models import Role, User
    from app.auth.security import hash_password
    from app.exams.models import Exam, ExamCandidate
    from app.organizations.models import Organization
    from app.questions.models import ExamPaper, ExamPaperItem, Question, question_hash

    roles = {r.name: r for r in db.query(Role).all()}
    for needed in ("admin", "examiner", "student"):
        if needed not in roles:
            sys.exit(f"The role '{needed}' does not exist. Run:  alembic upgrade head   (from the repo-clean folder)")

    org = db.query(Organization).filter(Organization.slug == ORG_SLUG).first()
    if not org:
        org = Organization(name="CampusCert Demo University", slug=ORG_SLUG, org_code=ORG_CODE,
                           contact_email=f"demo@{DOMAIN}", is_active=True)
        db.add(org)
        db.flush()
        print("  + organization created")

    users = {}
    for full_name, email, role in USERS:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(full_name=full_name, email=email, hashed_password=hash_password(PASSWORD),
                        is_active=True, role_id=roles[role].id, organization_id=org.id)
            db.add(user)
            db.flush()
            print(f"  + user {email} ({role})")
        users[email] = user
    examiner = users[f"demo.examiner@{DOMAIN}"]
    admin = users[f"demo.admin@{DOMAIN}"]

    questions = []
    for text, a, b, c, d, correct in QUESTIONS:
        digest = question_hash(SUBJECT, TOPIC, text)
        q = (db.query(Question)
             .filter(Question.organization_id == org.id, Question.created_by == examiner.id, Question.content_hash == digest)
             .first())
        if not q:
            q = Question(subject=SUBJECT, difficulty="easy", topic=TOPIC, question=text, option_a=a, option_b=b,
                         option_c=c, option_d=d, correct_option=correct, content_hash=digest,
                         organization_id=org.id, created_by=examiner.id)
            db.add(q)
            db.flush()
        questions.append(q)
    print(f"  = {len(questions)} questions ready")

    paper = db.query(ExamPaper).filter(ExamPaper.title == PAPER_TITLE, ExamPaper.organization_id == org.id).first()
    if not paper:
        paper = ExamPaper(title=PAPER_TITLE, instructions=INSTRUCTIONS, duration_minutes=15, organization_id=org.id)
        db.add(paper)
        db.flush()
        for position, q in enumerate(questions, start=1):
            db.add(ExamPaperItem(paper_id=paper.id, question_id=q.id, position=position, marks=1))
        print("  + paper created (10 questions, 1 mark each)")

    tomorrow = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)
    exam_specs = [
        dict(name=EXAM_NAMES[0], description="Ten multiple-choice questions on networking basics.",
             duration_minutes=15, status="ACTIVE", max_attempts=3, starts_at=None, ends_at=None),
        dict(name=EXAM_NAMES[1], description="Same questions but only one minute: leave it running to watch the exam submit and grade itself.",
             duration_minutes=1, status="ACTIVE", max_attempts=100, starts_at=None, ends_at=None),
        dict(name=EXAM_NAMES[2], description="Opens tomorrow, so students see it as upcoming and cannot start it.",
             duration_minutes=15, status="SCHEDULED", max_attempts=1, starts_at=tomorrow, ends_at=tomorrow + timedelta(hours=3)),
    ]
    for spec in exam_specs:
        exam = db.query(Exam).filter(Exam.organization_id == org.id, Exam.name == spec["name"]).first()
        if not exam:
            exam = Exam(organization_id=org.id, created_by_user_id=admin.id, instructions=INSTRUCTIONS, passing_score=50,
                        shuffle_questions=True, max_students=10, paper_id=paper.id, distribution={}, **spec)
            db.add(exam)
            db.flush()
            print(f"  + exam '{spec['name']}' ({spec['status']})")
        for email in STUDENT_EMAILS:
            has = (db.query(ExamCandidate).filter(ExamCandidate.exam_id == exam.id, ExamCandidate.user_id == users[email].id).first())
            if not has:
                db.add(ExamCandidate(exam_id=exam.id, user_id=users[email].id))
    db.commit()
    print("\nDone. Log in at http://localhost:5173/login with")
    print(f"  demo.student1@{DOMAIN}   password: {PASSWORD}")


def remove(db) -> None:
    from app.auth.models import User
    from app.exams.models import Exam, ExamCandidate
    from app.organizations.models import Organization
    from app.questions.models import ExamPaper, ExamPaperItem, Question

    org = db.query(Organization).filter(Organization.slug == ORG_SLUG).first()
    if not org:
        print("No demo data found. Nothing to remove.")
        return

    # Delete in dependency order, each step executed immediately (nothing waits for a later flush).
    exam_ids = [row[0] for row in db.query(Exam.id).filter(Exam.organization_id == org.id)]
    if exam_ids:
        # attempts, saved answers, the answer log and results go with their exams (ON DELETE CASCADE)
        db.query(ExamCandidate).filter(ExamCandidate.exam_id.in_(exam_ids)).delete(synchronize_session=False)
        db.query(Exam).filter(Exam.id.in_(exam_ids)).delete(synchronize_session=False)
    paper_ids = [row[0] for row in db.query(ExamPaper.id).filter(ExamPaper.organization_id == org.id)]
    if paper_ids:
        db.query(ExamPaperItem).filter(ExamPaperItem.paper_id.in_(paper_ids)).delete(synchronize_session=False)
        db.query(ExamPaper).filter(ExamPaper.id.in_(paper_ids)).delete(synchronize_session=False)
    db.query(Question).filter(Question.organization_id == org.id).delete(synchronize_session=False)
    db.query(User).filter(User.organization_id == org.id, User.email.like(f"%@{DOMAIN}")).delete(synchronize_session=False)

    left = db.query(User).filter(User.organization_id == org.id).count()
    if left == 0:
        db.query(Organization).filter(Organization.id == org.id).delete(synchronize_session=False)
    else:
        print(f"  (the demo organization stays: {left} other user(s) belong to it)")
    db.commit()
    print("Demo data removed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Add or remove the CampusCert demo data.")
    parser.add_argument("--remove", action="store_true", help="delete the demo data instead of adding it")
    parser.add_argument("--yes", action="store_true", help="do not ask for confirmation")
    args = parser.parse_args()

    from app.core.config import settings
    from app.core.database import SessionLocal

    if not args.yes:
        confirm(settings.DATABASE_URL)
    db = SessionLocal()
    try:
        (remove if args.remove else seed)(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
