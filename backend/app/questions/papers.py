"""Exam papers: choose questions by hand, or generate them randomly, then edit / print."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

# >>> same DB dependency as router.py
from app.auth.models import User
from app.core.database import get_db
from app.exams.constants import STATUS_ACTIVE, STATUS_SCHEDULED
from app.exams.models import Exam

from .access import bank_user, my_bank, org_scope, paper_reader, scoped
from .models import ExamPaper, ExamPaperItem, Question
from .schemas import PaperGenerate, PaperIn, PaperItemOut, PaperOut, PaperSummary
from .selection import select_random

router = APIRouter(tags=["exam papers"])


def _out(paper: ExamPaper) -> PaperOut:
    items = sorted(paper.items, key=lambda i: i.position)
    return PaperOut(
        id=paper.id, title=paper.title, instructions=paper.instructions,
        duration_minutes=paper.duration_minutes, created_at=paper.created_at,
        question_count=len(items), total_marks=sum(i.marks for i in items),
        items=[PaperItemOut(position=n, marks=i.marks, question=i.question) for n, i in enumerate(items, 1)],
    )


def _summary(paper: ExamPaper) -> PaperSummary:
    return PaperSummary(
        id=paper.id, title=paper.title, duration_minutes=paper.duration_minutes,
        created_at=paper.created_at, question_count=len(paper.items),
        total_marks=sum(i.marks for i in paper.items),
    )


def _get(db: Session, paper_id: int, user: User) -> ExamPaper:
    paper = scoped(db.query(ExamPaper), ExamPaper, user).filter(ExamPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(404, "Exam paper not found.")
    return paper


def _exams_using(db: Session, paper_id: int, statuses):
    return db.query(Exam).filter(Exam.paper_id == paper_id, Exam.status.in_(statuses)).all()


def _guard_in_use(db: Session, paper_id: int, statuses, action: str):
    """A paper that a scheduled / live exam depends on must not change under it."""
    exams = _exams_using(db, paper_id, statuses)
    if exams:
        names = ", ".join(f'"{e.name}"' for e in exams[:3])
        raise HTTPException(409, f"This paper is used by {names}. Detach it from the exam before you {action} it.")


def _write_items(db: Session, paper_id: int, pairs, user: User):
    """pairs = ordered list of (question_id, marks). Replaces everything in the paper."""
    seen, ordered = set(), []
    for qid, marks in pairs:                      # drop repeats, keep order
        if qid not in seen:
            seen.add(qid)
            ordered.append((qid, marks))
    # A question must come from the examiner's OWN bank, or already be in this paper (another examiner of
    # the organization put it there). Questions in other examiners' banks cannot be added.
    own = {q for (q,) in my_bank(db.query(Question.id), user).filter(Question.id.in_(seen))}
    in_paper_q = db.query(ExamPaperItem.question_id).filter(
        ExamPaperItem.paper_id == paper_id, ExamPaperItem.question_id.in_(seen))
    in_paper = {q for (q,) in in_paper_q}
    if (own | in_paper) != seen:
        raise HTTPException(422, "Some of those questions no longer exist. Refresh and try again.")
    db.query(ExamPaperItem).filter(ExamPaperItem.paper_id == paper_id).delete(synchronize_session=False)
    db.flush()
    db.add_all(ExamPaperItem(paper_id=paper_id, question_id=q, position=n, marks=m)
               for n, (q, m) in enumerate(ordered, 1))


@router.post("", response_model=PaperOut, status_code=201)
def create_paper(body: PaperIn, db: Session = Depends(get_db), user: User = Depends(bank_user)):
    """Teacher picked the questions by hand."""
    paper = ExamPaper(title=body.title, instructions=body.instructions or None,
                      duration_minutes=body.duration_minutes, organization_id=org_scope(user))
    db.add(paper)
    db.flush()
    _write_items(db, paper.id, [(i.question_id, i.marks) for i in body.items], user)
    db.commit()
    db.refresh(paper)
    return _out(paper)


@router.post("/generate", response_model=PaperOut, status_code=201)
def generate_paper(body: PaperGenerate, db: Session = Depends(get_db), user: User = Depends(bank_user)):
    """Pick random questions from the teacher's filters and save them as a paper."""
    items, requested, available, shortfall = select_random(db, body, my_bank(db.query(Question), user))
    if not items:
        raise HTTPException(409, "No questions match those filters, so no paper was made.")
    if shortfall and not body.allow_partial:
        detail = ", ".join(f"{v} more {k}" if k != "total" else f"{v} more" for k, v in shortfall.items())
        raise HTTPException(
            409, f"Only {len(items)} of the {requested} questions you asked for matched ({detail} needed). "
                 "Add more questions, loosen the filters, or tick 'Create anyway'.")
    paper = ExamPaper(title=body.title, instructions=body.instructions or None,
                      duration_minutes=body.duration_minutes, organization_id=org_scope(user))
    db.add(paper)
    db.flush()
    _write_items(db, paper.id, [(q.id, body.marks_each) for q in items], user)
    db.commit()
    db.refresh(paper)
    return _out(paper)


@router.get("", response_model=List[PaperSummary])
def list_papers(db: Session = Depends(get_db), user: User = Depends(paper_reader)):
    papers = scoped(db.query(ExamPaper), ExamPaper, user).options(selectinload(ExamPaper.items)) \
               .order_by(ExamPaper.created_at.desc(), ExamPaper.id.desc()).all()
    return [_summary(p) for p in papers]


@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(paper_id: int, db: Session = Depends(get_db), user: User = Depends(paper_reader)):
    out = _out(_get(db, paper_id, user))
    if user.role.name == "admin":          # admins see the questions and options, never the answers
        for item in out.items:
            item.question.correct_option = None
            item.question.solution = None
    return out


@router.put("/{paper_id}", response_model=PaperOut)
def update_paper(paper_id: int, body: PaperIn, db: Session = Depends(get_db), user: User = Depends(bank_user)):
    paper = _get(db, paper_id, user)
    _guard_in_use(db, paper.id, (STATUS_ACTIVE,), "edit")   # no edits while students are sitting the exam
    paper.title = body.title
    paper.instructions = body.instructions or None
    paper.duration_minutes = body.duration_minutes
    _write_items(db, paper.id, [(i.question_id, i.marks) for i in body.items], user)
    db.commit()
    db.refresh(paper)
    return _out(paper)


@router.delete("/{paper_id}", status_code=204)
def delete_paper(paper_id: int, db: Session = Depends(get_db), user: User = Depends(bank_user)):
    paper = _get(db, paper_id, user)
    _guard_in_use(db, paper.id, (STATUS_SCHEDULED, STATUS_ACTIVE), "delete")
    db.delete(paper)
    db.commit()
