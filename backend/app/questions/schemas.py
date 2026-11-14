from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    subject: str
    difficulty: str
    topic: str
    question: str
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_option: Optional[str] = None   # hidden from admins / never sent to students
    solution: Optional[str] = None
    created_at: Optional[datetime] = None


class QuestionPage(BaseModel):
    items: List[QuestionOut]
    total: int
    page: int
    page_size: int


class ImportError_(BaseModel):
    row: int
    reason: str


class ImportReport(BaseModel):
    imported: int
    duplicates: int
    errors: List[ImportError_]


class FilterOptions(BaseModel):
    subjects: List[str]
    topics: List[str]
    difficulties: List[str]


# ---------- exam papers ----------
class RandomRequest(BaseModel):
    """Where to pick from + how many. Give `count` (optionally with one `difficulty`),
    OR give `mix` such as {"easy": 3, "medium": 2, "hard": 1}."""
    subject: Optional[str] = None
    topics: List[str] = Field(default_factory=list)       # empty = all topics
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None
    count: Optional[int] = Field(None, ge=1, le=200)
    mix: Optional[Dict[str, int]] = None
    exclude_ids: List[int] = Field(default_factory=list)


class PaperItemIn(BaseModel):
    question_id: int
    marks: int = Field(1, ge=1, le=100)


class PaperIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(..., min_length=1, max_length=200)
    instructions: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)
    items: List[PaperItemIn] = Field(..., min_length=1, max_length=200)


class PaperGenerate(RandomRequest):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(..., min_length=1, max_length=200)
    instructions: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)
    marks_each: int = Field(1, ge=1, le=100)
    allow_partial: bool = False     # make a shorter paper if not enough questions match


class PaperItemOut(BaseModel):
    position: int
    marks: int
    question: QuestionOut


class PaperOut(BaseModel):
    id: int
    title: str
    instructions: Optional[str] = None
    duration_minutes: Optional[int] = None
    created_at: Optional[datetime] = None
    question_count: int
    total_marks: int
    items: List[PaperItemOut]


class PaperSummary(BaseModel):
    id: int
    title: str
    duration_minutes: Optional[int] = None
    created_at: Optional[datetime] = None
    question_count: int
    total_marks: int


class RandomResult(BaseModel):
    items: List[QuestionOut]
    requested: int
    returned: int
    available: int                                            # how many matched the filters
    shortfall: Dict[str, int] = Field(default_factory=dict)   # what could not be filled


class BulkDelete(BaseModel):
    """Delete ticked questions (`ids`), or EVERYTHING that matches the filters (`all_matching`).
    With all_matching and no filters this clears the whole question bank."""
    ids: List[int] = Field(default_factory=list)
    all_matching: bool = False
    subject: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[Literal["easy", "medium", "hard"]] = None
    q: Optional[str] = None


class BulkDeleteResult(BaseModel):
    deleted: int
