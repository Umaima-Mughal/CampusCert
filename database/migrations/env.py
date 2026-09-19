"""
database/migrations/env.py

Alembic reads this file to know:
  1. What the "target" schema should look like (your SQLAlchemy models)
  2. Which database to connect to (pulled from app.core.config, so the
     same DATABASE_URL from your .env is used everywhere — no duplication)

You shouldn't need to touch this file often. It's shared setup —
give the team a heads-up before changing it (README rule #2).
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Make the backend/ package importable from here ---
# This file lives at <repo_root>/database/migrations/env.py, but the
# actual app code lives at <repo_root>/backend/app/. Add backend/ to
# sys.path so `import app.core...` works no matter where alembic is run from.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings          # noqa: E402
from app.core.database import Base            # noqa: E402

# --- Import every model so Base.metadata knows about all tables ---
# As new modules are added (exams, questions, attempts, security,
# analytics), each owner should add their model import here too —
# otherwise autogenerate won't "see" their tables.
from app.auth.models import User, Role                 # noqa: E402,F401
from app.organizations.models import Organization       # noqa: E402,F401

# Alembic Config object, gives access to values in alembic.ini
config = context.config

# Inject the real DB URL from settings (from .env) instead of alembic.ini
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

# Interpret the config file for logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is what autogenerate compares your models against
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL scripts without a live DB connection (rarely used here)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the DB (Supabase Postgres) and apply migrations directly."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
