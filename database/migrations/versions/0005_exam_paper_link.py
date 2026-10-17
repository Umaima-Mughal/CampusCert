"""link exams to question papers + make the question bank per-organization (Member 3 x Member 2)

Revision ID: 0005_exam_paper_link
Revises: 1f56c62929c3

Additive. Nothing is dropped except the old *global* unique rule on
questions.content_hash, which becomes unique per organization.
Idempotent (IF NOT EXISTS) like the other question-bank migrations.

AFTER running this, assign your existing rows to an organization, otherwise they
stay invisible (everything is filtered by organization now):

    UPDATE questions    SET organization_id = (SELECT id FROM organizations WHERE org_code = 'CC-XXXXXX') WHERE organization_id IS NULL;
    UPDATE exam_papers  SET organization_id = (SELECT id FROM organizations WHERE org_code = 'CC-XXXXXX') WHERE organization_id IS NULL;
"""
from alembic import op

revision = "0005_exam_paper_link"
down_revision = "1f56c62929c3"
branch_labels = None
depends_on = None

UP = """
ALTER TABLE questions   ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
ALTER TABLE exam_papers ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
CREATE INDEX IF NOT EXISTS ix_questions_organization_id   ON questions   (organization_id);
CREATE INDEX IF NOT EXISTS ix_exam_papers_organization_id ON exam_papers (organization_id);

-- the same question may now exist once per organization
ALTER TABLE questions DROP CONSTRAINT IF EXISTS questions_content_hash_key;
ALTER TABLE questions DROP CONSTRAINT IF EXISTS uq_questions_content_hash;
ALTER TABLE questions DROP CONSTRAINT IF EXISTS uq_questions_org_content_hash;
ALTER TABLE questions ADD CONSTRAINT uq_questions_org_content_hash UNIQUE (organization_id, content_hash);

-- Member 2's exams point at a paper; deleting a paper just detaches it
ALTER TABLE exams ADD COLUMN IF NOT EXISTS paper_id INTEGER REFERENCES exam_papers(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS ix_exams_paper_id ON exams (paper_id);
"""

DOWN = """
DROP INDEX IF EXISTS ix_exams_paper_id;
ALTER TABLE exams DROP COLUMN IF EXISTS paper_id;
ALTER TABLE questions DROP CONSTRAINT IF EXISTS uq_questions_org_content_hash;
ALTER TABLE questions ADD CONSTRAINT questions_content_hash_key UNIQUE (content_hash);
DROP INDEX IF EXISTS ix_exam_papers_organization_id;
DROP INDEX IF EXISTS ix_questions_organization_id;
ALTER TABLE exam_papers DROP COLUMN IF EXISTS organization_id;
ALTER TABLE questions   DROP COLUMN IF EXISTS organization_id;
"""


def upgrade():
    op.execute(UP)


def downgrade():
    op.execute(DOWN)
