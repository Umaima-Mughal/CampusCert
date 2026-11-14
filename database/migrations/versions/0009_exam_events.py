
"""Add exam integrity events for Member 5.

Revision ID: 0009_exam_events
Revises: 0008_student_attempts
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0009_exam_events"
down_revision = "0008_student_attempts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "exam_events",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "attempt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "exam_attempts.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),

        sa.Column(
            "event_type",
            sa.String(length=40),
            nullable=False,
        ),

        sa.Column(
            "occurred_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "note",
            sa.Text(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_exam_events_attempt_time",
        "exam_events",
        ["attempt_id", "occurred_at"],
    )


def downgrade():
    op.drop_index(
        "ix_exam_events_attempt_time",
        table_name="exam_events",
    )

    op.drop_table("exam_events")
