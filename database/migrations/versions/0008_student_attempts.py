"""student exam attempts, saved answers, answer log and results (Member 4)

Revision ID: 0008_student_attempts
Revises: 0007_private_question_banks

Additive and idempotent: it only creates new tables, nothing existing is changed.
question_id has no foreign key on purpose: examiners may edit or delete questions
later, and a student's answer history must survive that (it is the audit trail).
"""
from alembic import op

revision = "0008_student_attempts"
down_revision = "0007_private_question_banks"
branch_labels = None
depends_on = None

UP = """
CREATE TABLE IF NOT EXISTS exam_attempts (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES users(id),
    attempt_number INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    started_at TIMESTAMP NOT NULL DEFAULT now(),
    expires_at TIMESTAMP NOT NULL,
    submitted_at TIMESTAMP,
    layout JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_attempt_exam_candidate_number UNIQUE (exam_id, candidate_id, attempt_number)
);
CREATE INDEX IF NOT EXISTS ix_exam_attempts_exam_id ON exam_attempts (exam_id);
CREATE INDEX IF NOT EXISTS ix_exam_attempts_candidate_id ON exam_attempts (candidate_id);

CREATE TABLE IF NOT EXISTS candidate_answers (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    attempt_id UUID NOT NULL REFERENCES exam_attempts(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL,
    selected_option VARCHAR(1),
    marked_for_review BOOLEAN NOT NULL DEFAULT FALSE,
    answered_at TIMESTAMP,
    CONSTRAINT uq_candidate_answer_attempt_question UNIQUE (attempt_id, question_id),
    CONSTRAINT ck_candidate_answers_option CHECK (selected_option IS NULL OR selected_option IN ('A','B','C','D'))
);
CREATE INDEX IF NOT EXISTS ix_candidate_answers_attempt_id ON candidate_answers (attempt_id);

CREATE TABLE IF NOT EXISTS answer_log (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    attempt_id UUID NOT NULL REFERENCES exam_attempts(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL,
    selected_option VARCHAR(1),
    marked_for_review BOOLEAN NOT NULL DEFAULT FALSE,
    saved_at TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_answer_log_attempt_id ON answer_log (attempt_id);

CREATE TABLE IF NOT EXISTS results (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    attempt_id UUID NOT NULL UNIQUE REFERENCES exam_attempts(id) ON DELETE CASCADE,
    exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES users(id),
    total_marks INTEGER NOT NULL DEFAULT 0,
    obtained_marks INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0,
    incorrect_count INTEGER NOT NULL DEFAULT 0,
    unanswered_count INTEGER NOT NULL DEFAULT 0,
    percentage DOUBLE PRECISION NOT NULL DEFAULT 0,
    passed BOOLEAN,
    breakdown JSONB NOT NULL DEFAULT '[]'::jsonb,
    graded_at TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_results_exam_id ON results (exam_id);
CREATE INDEX IF NOT EXISTS ix_results_candidate_id ON results (candidate_id);
"""

DOWN = """
DROP TABLE IF EXISTS results;
DROP TABLE IF EXISTS answer_log;
DROP TABLE IF EXISTS candidate_answers;
DROP TABLE IF EXISTS exam_attempts;
"""


def upgrade():
    op.execute(UP)


def downgrade():
    op.execute(DOWN)
