import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.database import get_db
from app.exams.constants import STATUS_ACTIVE, STATUS_SCHEDULED
from app.exams.models import Exam

from .access import bank_user, org_scope, same_org, scoped
from .models import ExamPaper, ExamPaperItem, Question, question_hash
from .papers import router as papers_router
from .parser import parse_file
from .schemas import (
    BulkDelete, BulkDeleteResult, FilterOptions, ImportReport, QuestionPage, RandomRequest, RandomResult,
)
from .selection import select_random

log = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/questions", tags=["question bank"])
router.include_router(papers_router, prefix="/papers")   # /questions/papers/...

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/import", response_model=ImportReport)
async def import_questions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(bank_user),
):
    org_id = org_scope(user)
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File is larger than 10 MB.")
    try:
        parsed = parse_file(file.filename or "", data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except ImportError as e:
        # pdfplumber (PDF) or openpyxl (Excel) is not installed in the Python running the backend
        log.exception("Import failed: missing package for %s", file.filename)
        raise HTTPException(
            500,
            f"The server is missing the '{e.name}' package needed to read this file type. "
            "Stop the backend, run: python -m pip install pdfplumber openpyxl  then start it again. "
            "(CSV files work without it.)",
        )
    except Exception:
        log.exception("Could not read uploaded file %s", file.filename)   # full details in the backend terminal
        raise HTTPException(422, "Could not read this file. Check that it isn't corrupted or password-protected.")

    # All or nothing: a file with a missing column, a blank value or a bad row is refused entirely.
    if parsed.errors or not parsed.rows:
        raise HTTPException(422, detail={
            "message": "This file is not in the correct format, so nothing was imported. Please upload a file "
                       "with the correct format: every question needs a subject, difficulty, topic, question, "
                       "four options, the correct answer and a solution.",
            "errors": parsed.errors[:50] or [{"row": 1, "reason": "The file contains no questions."}],
            "total_errors": len(parsed.errors) or 1,
        })

    # hashes already in this organization + hashes repeated inside the same file
    seen = {h for (h,) in db.query(Question.content_hash).filter(same_org(Question, org_id)).all()}
    new_rows, duplicates = [], 0
    for r in parsed.rows:
        h = question_hash(r["subject"], r["topic"], r["question"])
        if h in seen:
            duplicates += 1
            continue
        seen.add(h)
        new_rows.append(Question(**r, content_hash=h, organization_id=org_id))

    db.add_all(new_rows)
    db.commit()
    return ImportReport(imported=len(new_rows), duplicates=duplicates, errors=parsed.errors)


def _apply_filters(query, subject=None, topic=None, difficulty=None, q=None):
    if subject:
        query = query.filter(Question.subject == subject)
    if topic:
        query = query.filter(Question.topic == topic)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    if q:
        query = query.filter(Question.question.ilike(f"%{q}%"))
    return query


@router.get("", response_model=QuestionPage)
def list_questions(
    subject: Optional[str] = None,
    topic: Optional[str] = None,
    difficulty: Optional[str] = Query(None, pattern="^(easy|medium|hard)$"),
    q: Optional[str] = Query(None, description="Search inside question text"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(bank_user),
):
    query = _apply_filters(scoped(db.query(Question), Question, user), subject, topic, difficulty, q)
    total = query.count()
    items = (query.order_by(Question.subject, Question.topic, Question.id)
                  .offset((page - 1) * page_size).limit(page_size).all())
    return QuestionPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/filters", response_model=FilterOptions)
def filter_options(
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(bank_user),
):
    """Dropdown values. Topics narrow to the chosen subject."""
    subjects = [s for (s,) in scoped(db.query(Question.subject), Question, user).distinct().order_by(Question.subject)]
    tq = scoped(db.query(Question.topic), Question, user).distinct()
    if subject:
        tq = tq.filter(Question.subject == subject)
    topics = [t for (t,) in tq.order_by(Question.topic)]
    return FilterOptions(subjects=subjects, topics=topics, difficulties=["easy", "medium", "hard"])


@router.post("/random", response_model=RandomResult)
def random_questions(
    req: RandomRequest,
    db: Session = Depends(get_db),
    user: User = Depends(bank_user),
):
    """Random questions that match subject / topics / difficulty and are not in `exclude_ids`.
    Used by the "Change question" button in the exam paper editor."""
    items, requested, available, shortfall = select_random(db, req, scoped(db.query(Question), Question, user))
    return RandomResult(items=items, requested=requested, returned=len(items),
                        available=available, shortfall=shortfall)


def _locked_exam_names(db: Session, question_ids):
    """Exams (scheduled / live) whose paper contains any of these questions."""
    rows = (db.query(Exam.name)
              .join(ExamPaper, ExamPaper.id == Exam.paper_id)
              .join(ExamPaperItem, ExamPaperItem.paper_id == ExamPaper.id)
              .filter(Exam.status.in_((STATUS_SCHEDULED, STATUS_ACTIVE)),
                      ExamPaperItem.question_id.in_(question_ids))
              .distinct().all())
    return [n for (n,) in rows]


def _refuse_if_locked(db: Session, question_ids):
    names = _locked_exam_names(db, question_ids)
    if names:
        shown = ", ".join(f'"{n}"' for n in names[:3])
        raise HTTPException(
            409,
            f"Some of these questions are in a paper used by a scheduled or live exam ({shown}). "
            "Ask the admin to detach that paper from the exam first.",
        )


def _delete_questions(db: Session, user: User, ids: list) -> int:
    """Deletes the questions (inside the user's organization), removes them from papers,
    and drops papers that end up empty. Returns how many questions were deleted."""
    deleted = 0
    for start in range(0, len(ids), 1000):
        chunk = ids[start:start + 1000]
        _refuse_if_locked(db, chunk)
        db.query(ExamPaperItem).filter(ExamPaperItem.question_id.in_(chunk)).delete(synchronize_session=False)
        deleted += (scoped(db.query(Question), Question, user)
                    .filter(Question.id.in_(chunk)).delete(synchronize_session=False))
    # a paper with no questions left is useless; removing it also detaches it from draft exams
    empty = scoped(db.query(ExamPaper), ExamPaper, user).filter(
        ~ExamPaper.id.in_(select(ExamPaperItem.paper_id))).all()
    for paper in empty:
        db.delete(paper)
    db.commit()
    return deleted


@router.post("/bulk-delete", response_model=BulkDeleteResult)
def bulk_delete_questions(
    body: BulkDelete,
    db: Session = Depends(get_db),
    user: User = Depends(bank_user),
):
    """Delete the ticked questions, or every question matching the filters (all_matching=true)."""
    if body.all_matching:
        query = _apply_filters(scoped(db.query(Question.id), Question, user),
                               body.subject, body.topic, body.difficulty, body.q)
        ids = [i for (i,) in query.all()]
    else:
        if not body.ids:
            raise HTTPException(422, "Select at least one question.")
        ids = list(set(body.ids))
    if not ids:
        return BulkDeleteResult(deleted=0)
    return BulkDeleteResult(deleted=_delete_questions(db, user, ids))


@router.delete("/{question_id}", status_code=204)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(bank_user),
):
    obj = scoped(db.query(Question), Question, user).filter(Question.id == question_id).first()
    if not obj:
        raise HTTPException(404, "Question not found.")
    _refuse_if_locked(db, [question_id])
    # remove it from any exam papers first (works on every database)
    db.query(ExamPaperItem).filter(ExamPaperItem.question_id == question_id).delete(synchronize_session=False)
    db.delete(obj)
    db.commit()
