"""
app/core/utils.py

Small shared helper functions used across multiple modules
(not specific to auth or organizations).
"""

import uuid
from datetime import datetime


def new_uuid() -> uuid.UUID:
    """Generate a new unique ID — used anywhere a model needs one manually."""
    return uuid.uuid4()


def utc_now() -> datetime:
    """Consistent 'current time' helper so every module stamps time the same way."""
    return datetime.utcnow()


def to_camel_case(snake_str: str) -> str:
    """
    Converts python_style_names to camelCaseNames.
    Handy when building JSON responses the frontend expects in camelCase.
    """
    parts = snake_str.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])
