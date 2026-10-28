"""every examiner gets a private question bank (Member 3)

Revision ID: 0007_private_question_banks
Revises: 0006_mcq_columns

questions.created_by was an INTEGER that nothing could fill, because user ids are UUIDs.
It becomes the owning examiner (users.id), and the "same question once" rule becomes
"once per examiner", so two examiners may each keep their own copy.

Existing questions have no owner (NULL), so examiners will not see them until you give
them one. For example, to give every unowned question of one organization to one examiner:

    UPDATE questions SET created_by = '<examiner users.id>'
    WHERE organization_id = '<organizations.id>' AND created_by IS NULL;

(add  AND subject = 'Physics'  to split a bank between examiners)
"""
from alembic import op

revision = "0007_private_question_banks"
down_revision = "0006_mcq_columns"
branch_labels = None
depends_on = None

UP = """
DO $$
BEGIN
    IF (SELECT data_type FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = 'questions' AND column_name = 'created_by') <> 'uuid' THEN
        ALTER TABLE questions ALTER COLUMN created_by TYPE UUID USING CAST(NULL AS UUID);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_questions_created_by') THEN
        ALTER TABLE questions
            ADD CONSTRAINT fk_questions_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_questions_created_by ON questions (created_by);

ALTER TABLE questions DROP CONSTRAINT IF EXISTS uq_questions_org_content_hash;
ALTER TABLE questions DROP CONSTRAINT IF EXISTS uq_questions_owner_content_hash;
ALTER TABLE questions ADD CONSTRAINT uq_questions_owner_content_hash UNIQUE (organization_id, created_by, content_hash);
"""

DOWN = """
ALTER TABLE questions DROP CONSTRAINT IF EXISTS uq_questions_owner_content_hash;
ALTER TABLE questions ADD CONSTRAINT uq_questions_org_content_hash UNIQUE (organization_id, content_hash);
ALTER TABLE questions DROP CONSTRAINT IF EXISTS fk_questions_created_by;
DROP INDEX IF EXISTS ix_questions_created_by;
ALTER TABLE questions ALTER COLUMN created_by TYPE INTEGER USING CAST(NULL AS INTEGER);
"""


def upgrade():
    op.execute(UP)


def downgrade():
    op.execute(DOWN)
