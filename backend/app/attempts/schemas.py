"""app/attempts/schemas.py  (Member 4): what the student's browser sends us."""
import uuid
from typing import Literal

from pydantic import BaseModel


class StartAttemptIn(BaseModel):
    exam_id: uuid.UUID


class AnswerIn(BaseModel):
    """Autosave body. Send only what changed:
       {"question_id": 5, "selected_option": "B"}        choose / change an answer
       {"question_id": 5, "selected_option": null}       clear the answer
       {"question_id": 5, "marked_for_review": true}     flag the question, answer untouched"""
    question_id: int
    selected_option: Literal["A", "B", "C", "D"] | None = None
    marked_for_review: bool | None = None
