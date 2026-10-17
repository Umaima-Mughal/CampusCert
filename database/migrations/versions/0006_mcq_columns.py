"""multiple-choice questions: four options, the correct one, and a solution (Member 3)

Revision ID: 0006_mcq_columns
Revises: 0005_exam_paper_link

Additive and idempotent. Old questions keep working (the new columns are nullable).
"""
from alembic import op

revision = "0006_mcq_columns"
down_revision = "0005_exam_paper_link"
branch_labels = None
depends_on = None

UP = """
ALTER TABLE questions ADD COLUMN IF NOT EXISTS option_a TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS option_b TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS option_c TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS option_d TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS correct_option VARCHAR(1);
ALTER TABLE questions ADD COLUMN IF NOT EXISTS solution TEXT;
ALTER TABLE questions DROP CONSTRAINT IF EXISTS ck_questions_correct_option;
ALTER TABLE questions ADD CONSTRAINT ck_questions_correct_option
    CHECK (correct_option IS NULL OR correct_option IN ('A','B','C','D'));
"""

DOWN = """
ALTER TABLE questions DROP CONSTRAINT IF EXISTS ck_questions_correct_option;
ALTER TABLE questions DROP COLUMN IF EXISTS solution;
ALTER TABLE questions DROP COLUMN IF EXISTS correct_option;
ALTER TABLE questions DROP COLUMN IF EXISTS option_d;
ALTER TABLE questions DROP COLUMN IF EXISTS option_c;
ALTER TABLE questions DROP COLUMN IF EXISTS option_b;
ALTER TABLE questions DROP COLUMN IF EXISTS option_a;
"""


def upgrade():
    op.execute(UP)


def downgrade():
    op.execute(DOWN)
