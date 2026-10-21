"""create questions table (Member 3)

Revision ID: 5eae25ee27e1
Revises: 0004_org_code_max_students
"""
from alembic import op

revision = "5eae25ee27e1"
down_revision = '0004_org_code_max_students'
branch_labels = None
depends_on = None

# IF NOT EXISTS makes this safe even if the table was already created by hand.
SQL = """
CREATE TABLE IF NOT EXISTS questions (
    id           SERIAL PRIMARY KEY,
    subject      VARCHAR(120) NOT NULL,
    difficulty   VARCHAR(10)  NOT NULL CHECK (difficulty IN ('easy','medium','hard')),
    topic        VARCHAR(160) NOT NULL,
    question     TEXT         NOT NULL,
    content_hash VARCHAR(64)  NOT NULL UNIQUE,
    created_by   INTEGER,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_questions_subject    ON questions (subject);
CREATE INDEX IF NOT EXISTS ix_questions_topic      ON questions (topic);
CREATE INDEX IF NOT EXISTS ix_questions_difficulty ON questions (difficulty);
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS questions")
