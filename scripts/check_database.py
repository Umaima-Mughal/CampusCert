"""
scripts/check_database.py

READ-ONLY health check of the database the backend is configured to use.
It changes nothing. It tells you, in plain words, whether:

  1. the backend can connect to the database,
  2. the database is on the latest migration (alembic head),
  3. every table the code expects exists, including the Member 4 tables
     (exam_attempts, candidate_answers, answer_log, results),
  4. every column the code expects exists in those tables,
  5. the default roles (student, examiner, admin, super_admin) are seeded.

Run it from the backend folder, with the virtual environment active:

    cd backend
    python ..\\scripts\\check_database.py

Exit code 0 = everything fine, 1 = something needs fixing (the message says what).
"""
import importlib
import pkgutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import inspect, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

problems: list[str] = []


def ok(message: str) -> None:
    print(f"  [OK]   {message}")


def fail(message: str, fix: str | None = None) -> None:
    print(f"  [FAIL] {message}")
    if fix:
        print(f"         -> {fix}")
    problems.append(message)


def load_all_models() -> list[str]:
    """Import app/<module>/models.py for every module so all tables are registered."""
    import app

    loaded = []
    for pkg in pkgutil.iter_modules(app.__path__):
        if not pkg.ispkg:
            continue
        name = f"app.{pkg.name}.models"
        try:
            importlib.import_module(name)
            loaded.append(name)
        except ModuleNotFoundError as exc:
            if exc.name != name:  # a real missing package inside a models file, not "no models file"
                raise
    return loaded


def main() -> int:
    from app.core.config import settings
    from app.core.database import Base, engine

    load_all_models()
    url = make_url(settings.DATABASE_URL)
    print("CampusCert database check")
    print(f"  database: {url.drivername} on {url.host or 'local file'} / {url.database}  (user: {url.username})")
    print()

    # ---- 1. connection
    print("1. Connection")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        ok("connected to the database")
    except Exception as exc:  # noqa: BLE001
        fail(
            f"cannot connect: {str(exc).splitlines()[0][:160]}",
            "check DATABASE_URL in backend\\.env, your internet connection, and that the "
            "Supabase project is not paused",
        )
        print("\nStopping here: nothing else can be checked without a connection.")
        return 1

    insp = inspect(engine)
    tables_in_db = set(insp.get_table_names())

    # ---- 2. migrations
    print("\n2. Migrations")
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        cfg = Config(str(ROOT / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "database" / "migrations"))
        scripts = ScriptDirectory.from_config(cfg)
        head = scripts.get_current_head()
        known = {rev.revision for rev in scripts.walk_revisions()}
    except Exception as exc:  # noqa: BLE001
        head, known = None, set()
        fail(f"could not read the migration files: {exc}")

    current = None
    if "alembic_version" in tables_in_db:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT version_num FROM alembic_version")).first()
            current = row[0] if row else None
    if head is not None:
        if current is None:
            fail("the database has no migration version yet", "run:  alembic upgrade head   (from the repo-clean folder)")
        elif current == head:
            ok(f"database is on the latest migration ({current})")
        elif current in known:
            fail(f"database is on {current} but the latest is {head}", "run:  alembic upgrade head   (from the repo-clean folder)")
        else:
            fail(
                f"database is on {current}, which is NOT in your migrations folder",
                "your code is older than the database: get the newest project files (a teammate added a migration)",
            )

    # ---- 3 + 4. tables and columns
    print("\n3. Tables and columns the code expects")
    expected = Base.metadata.tables
    missing_tables = sorted(name for name in expected if name not in tables_in_db)
    for name in sorted(expected):
        if name in missing_tables:
            fail(f"table '{name}' is missing", "run:  alembic upgrade head   (from the repo-clean folder)")
            continue
        db_columns = {col["name"] for col in insp.get_columns(name)}
        missing_cols = sorted(col.name for col in expected[name].columns if col.name not in db_columns)
        if missing_cols:
            fail(f"table '{name}' is missing columns: {', '.join(missing_cols)}", "run:  alembic upgrade head")
        else:
            ok(f"{name}")
    member4 = ["exam_attempts", "candidate_answers", "answer_log", "results"]
    if all(t in tables_in_db for t in member4):
        ok("Member 4 tables are all present (exam_attempts, candidate_answers, answer_log, results)")

    # ---- 5. roles
    print("\n4. Default roles")
    if "roles" in tables_in_db:
        with engine.connect() as conn:
            names = {r[0] for r in conn.execute(text("SELECT name FROM roles"))}
        for role in ("student", "examiner", "admin", "super_admin"):
            if role in names:
                ok(f"role '{role}' exists")
            else:
                fail(f"role '{role}' is missing", "run:  alembic upgrade head  (migration 0002 seeds the roles)")

    # ---- row counts (information only)
    print("\n5. What is stored right now (information only)")
    with engine.connect() as conn:
        for name in ("organizations", "users", "exams", "exam_candidates", "questions", "exam_papers",
                     "exam_attempts", "candidate_answers", "answer_log", "results"):
            if name in tables_in_db:
                count = conn.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar()
                print(f"         {name:<18} {count}")

    print()
    if problems:
        print(f"RESULT: {len(problems)} problem(s) found. Fix the lines marked [FAIL] above.")
        return 1
    print("RESULT: the database is correct. All tables and columns the code needs are there.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
