"""add exams and exam_candidates

Revision ID: 0003_exams
Revises: 0002_seed_default_roles
Create Date: 2026-09-24

Additive schema for Member 2 exam management. Does not alter or drop
existing tables. Member 1 should review before merging to develop.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_exams"
down_revision = "0002_seed_default_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("instructions", sa.String(length=5000), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
        sa.Column("starts_at", sa.DateTime(), nullable=True),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("passing_score", sa.Integer(), nullable=True),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("shuffle_questions", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("late_join_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "distribution",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], name="fk_exams_organization_id"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], name="fk_exams_created_by_user_id"
        ),
    )
    op.create_index("ix_exams_organization_id", "exams", ["organization_id"])
    op.create_index(
        "ix_exams_organization_status", "exams", ["organization_id", "status"]
    )

    op.create_table(
        "exam_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("exam_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["exam_id"],
            ["exams.id"],
            name="fk_exam_candidates_exam_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_exam_candidates_user_id"
        ),
        sa.UniqueConstraint("exam_id", "user_id", name="uq_exam_candidates_exam_user"),
    )
    op.create_index("ix_exam_candidates_exam_id", "exam_candidates", ["exam_id"])
    op.create_index("ix_exam_candidates_user_id", "exam_candidates", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_exam_candidates_user_id", table_name="exam_candidates")
    op.drop_index("ix_exam_candidates_exam_id", table_name="exam_candidates")
    op.drop_table("exam_candidates")
    op.drop_index("ix_exams_organization_status", table_name="exams")
    op.drop_index("ix_exams_organization_id", table_name="exams")
    op.drop_table("exams")
