"""Shared exam status values used by routes, services, and schemas."""

STATUS_DRAFT = "DRAFT"
STATUS_SCHEDULED = "SCHEDULED"
STATUS_ACTIVE = "ACTIVE"
STATUS_CLOSED = "CLOSED"
STATUS_ARCHIVED = "ARCHIVED"

EXAM_STATUSES = (
    STATUS_DRAFT,
    STATUS_SCHEDULED,
    STATUS_ACTIVE,
    STATUS_CLOSED,
    STATUS_ARCHIVED,
)

# Lifecycle transitions owned by Member 2. Member 4 reads ACTIVE/CLOSED
# exams when starting or closing attempts; Member 5 reads ACTIVE exams
# for live integrity monitoring.
ALLOWED_TRANSITIONS = {
    STATUS_DRAFT: {STATUS_SCHEDULED, STATUS_ACTIVE, STATUS_ARCHIVED},
    STATUS_SCHEDULED: {STATUS_DRAFT, STATUS_ACTIVE, STATUS_CLOSED},
    STATUS_ACTIVE: {STATUS_SCHEDULED, STATUS_CLOSED},
    STATUS_CLOSED: {STATUS_ARCHIVED},
    STATUS_ARCHIVED: set(),
}

ADMIN_ROLES = ("admin", "super_admin")
STUDENT_ROLE = "student"
