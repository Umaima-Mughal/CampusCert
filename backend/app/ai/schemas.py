from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.questions.schemas import PaperOut


class AIPaperRequest(BaseModel):
    """The examiner only has to write `prompt`. The rest is optional."""
    model_config = ConfigDict(str_strip_whitespace=True)
    prompt: str = Field(..., min_length=8, max_length=2000,
                        description="e.g. '20 MCQs on Operating Systems, 40% easy, 40% medium, 20% hard'")
    question_count: Optional[int] = Field(None, ge=1, le=100, description="Leave empty to let the prompt decide.")
    title: Optional[str] = Field(None, max_length=200)
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)
    marks_each: int = Field(1, ge=1, le=100)


class AIPaperOut(PaperOut):
    requested: int
    skipped: int = 0                 # questions the AI wrote badly and we dropped
    ai_model: str = ""
    warnings: List[str] = Field(default_factory=list)


class AIStatus(BaseModel):
    configured: bool
    model: str
    max_questions: int
