"""create exam_papers and exam_paper_items (Member 3)

Revision ID: 1f56c62929c3
Revises: 5eae25ee27e1
"""
from alembic import op

revision = "1f56c62929c3"
down_revision = '5eae25ee27e1'
branch_labels = None
depends_on = None

# IF NOT EXISTS makes this safe even if the tables were already created by hand.
SQL = """
CREATE TABLE IF NOT EXISTS exam_papers (
    id               SERIAL PRIMARY KEY,
    title            VARCHAR(200) NOT NULL,
    instructions     TEXT,
    duration_minutes INTEGER,
    created_by       INTEGER,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS exam_paper_items (
    id          SERIAL PRIMARY KEY,
    paper_id    INTEGER NOT NULL REFERENCES exam_papers(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    position    INTEGER NOT NULL,
    marks       INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT uq_paper_question UNIQUE (paper_id, question_id)
);
CREATE INDEX IF NOT EXISTS ix_exam_paper_items_paper ON exam_paper_items (paper_id);
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS exam_paper_items")
    op.execute("DROP TABLE IF EXISTS exam_papers")
