"""Helpers for organization onboarding and user-facing org codes."""

import re
import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.organizations.models import Organization

# User-facing codes look like CC-7K4Q2M. Internal UUID remains the PK.
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ORG_CODE_PREFIX = "CC-"


def normalize_org_code(raw: str | None) -> str:
    if raw is None:
        return ""
    return re.sub(r"\s+", "", str(raw).strip().upper())


def generate_org_code() -> str:
    body = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))
    return f"{ORG_CODE_PREFIX}{body}"


def slug_from_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    slug = slug[:80] or "organization"
    return slug


def unique_org_code(db: Session) -> str:
    for _ in range(20):
        code = generate_org_code()
        exists = db.query(Organization.id).filter(Organization.org_code == code).first()
        if not exists:
            return code
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate a unique organization code",
    )


def unique_slug(db: Session, name: str) -> str:
    base = slug_from_name(name)
    slug = base
    suffix = 2
    while db.query(Organization.id).filter(Organization.slug == slug).first():
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug


def get_active_org_by_code(db: Session, org_code: str) -> Organization:
    code = normalize_org_code(org_code)
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization ID / Org Code is required",
        )
    org = db.query(Organization).filter(Organization.org_code == code).first()
    if not org or not org.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or inactive Organization ID. Check the Org Code and try again.",
        )
    return org


def onboard_organization(db: Session, name: str, contact_email: str) -> Organization:
    org = Organization(
        name=name.strip(),
        slug=unique_slug(db, name),
        contact_email=contact_email,
        org_code=unique_org_code(db),
        is_active=True,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org
