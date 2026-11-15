"""Examiner-side AI: write a prompt, get a ready exam paper. Only examiners (and super admins) can use it."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.database import get_db
from app.questions.access import bank_user
from app.questions.papers import _out

from .config import get_ai_settings
from .groq_client import GroqError
from .schemas import AIPaperOut, AIPaperRequest, AIStatus
from .service import build_ai_paper

router = APIRouter(prefix="/ai", tags=["AI paper generator"])


@router.get("/status", response_model=AIStatus)
def ai_status(user: User = Depends(bank_user)):
    cfg = get_ai_settings()
    return AIStatus(configured=bool(cfg.api_key), model=cfg.GROQ_MODEL, max_questions=cfg.AI_MAX_QUESTIONS)


@router.post("/generate-paper", response_model=AIPaperOut, status_code=201)
def generate_paper(body: AIPaperRequest, db: Session = Depends(get_db), user: User = Depends(bank_user)):
    """The examiner writes a prompt; the AI writes the questions, saves them in the examiner's own
    question bank and creates the exam paper from them."""
    try:
        paper, requested, skipped, warnings, model = build_ai_paper(db, user, body)
    except GroqError as e:
        db.rollback()
        raise HTTPException(e.status if e.status in (429, 503, 504) else 502, e.message)
    out = _out(paper)
    return AIPaperOut(**out.model_dump(), requested=requested, skipped=skipped, ai_model=model, warnings=warnings)
