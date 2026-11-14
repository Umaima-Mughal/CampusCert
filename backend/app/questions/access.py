"""Who may use the question bank, and which organization's data they see.

Member 3 module. Reuses Member 1's require_role(); no changes to auth code.
"""
from fastapi import HTTPException

from app.auth.dependencies import require_role
from app.auth.models import User

from .models import Question

# Examiners build the question bank and papers (create / edit / delete / import).
bank_user = require_role("examiner", "super_admin")

# Admins only READ papers (to assign one to an exam). Examiners may read too.
paper_reader = require_role("admin", "super_admin", "examiner")


def org_scope(user: User):
    """Organization this user works inside.
    None only for a super_admin who is not tied to an organization (sees everything)."""
    if user.role.name == "super_admin":
        return user.organization_id
    if not user.organization_id:
        raise HTTPException(400, "Your account is not assigned to an organization.")
    return user.organization_id


def scoped(query, model, user: User):
    """Limit a query to the user's organization."""
    org_id = org_scope(user)
    return query if org_id is None else query.filter(model.organization_id == org_id)


def same_org(model, org_id):
    """Filter for the bucket new rows are written into (used for duplicate checks)."""
    return model.organization_id.is_(None) if org_id is None else model.organization_id == org_id


def my_bank(query, user: User):
    """The questions this user may see and use.
    - examiner: only the questions they imported themselves (every examiner has a PRIVATE question bank)
    - super_admin: every question of their organization
    Papers are different: they are shared with every examiner of the organization (see `scoped`)."""
    query = scoped(query, Question, user)
    if user.role.name == "examiner":
        query = query.filter(Question.created_by == user.id)
    return query
