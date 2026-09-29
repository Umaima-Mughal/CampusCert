"""seed default roles

Revision ID: 0002_seed_default_roles
Revises: 0001_initial_schema
Create Date: 2026-09-12
"""
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import table, column
from datetime import datetime

revision = "0002_seed_default_roles"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

# A lightweight "view" of the roles table just for this data insert —
# we don't need the full ORM model, just enough to run an INSERT.
roles_table = table(
    "roles",
    column("id", postgresql.UUID(as_uuid=True)),
    column("created_at", sa.DateTime),
    column("updated_at", sa.DateTime),
    column("name", sa.String),
    column("description", sa.String),
)

DEFAULT_ROLES = ["student", "examiner", "admin", "super_admin"]


def upgrade() -> None:
    now = datetime.utcnow()
    op.bulk_insert(
        roles_table,
        [
            {
                "id": uuid.uuid4(),
                "created_at": now,
                "updated_at": now,
                "name": role_name,
                "description": None,
            }
            for role_name in DEFAULT_ROLES
        ],
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        roles_table.delete().where(roles_table.c.name.in_(DEFAULT_ROLES))
    )
