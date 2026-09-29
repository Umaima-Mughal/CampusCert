"""add organization org_code and exam max_students

Revision ID: 0004_org_code_max_students
Revises: 0003_exams
Create Date: 2026-09-26

Additive only. Does not modify 0001–0003 or drop existing tables.
"""
import secrets

from alembic import op
import sqlalchemy as sa

revision = "0004_org_code_max_students"
down_revision = "0003_exams"
branch_labels = None
depends_on = None

_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _new_code() -> str:
    body = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))
    return f"CC-{body}"


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("org_code", sa.String(length=32), nullable=True),
    )

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id FROM organizations WHERE org_code IS NULL")).fetchall()
    used = set()
    for row in rows:
        code = _new_code()
        while code in used:
            code = _new_code()
        used.add(code)
        conn.execute(
            sa.text("UPDATE organizations SET org_code = :code WHERE id = :id"),
            {"code": code, "id": row[0]},
        )

    op.alter_column("organizations", "org_code", nullable=False)
    op.create_unique_constraint("uq_organizations_org_code", "organizations", ["org_code"])
    op.create_index("ix_organizations_org_code", "organizations", ["org_code"])

    op.add_column(
        "exams",
        sa.Column(
            "max_students",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.alter_column("exams", "max_students", server_default=None)


def downgrade() -> None:
    op.drop_column("exams", "max_students")
    op.drop_index("ix_organizations_org_code", table_name="organizations")
    op.drop_constraint("uq_organizations_org_code", "organizations", type_="unique")
    op.drop_column("organizations", "org_code")
