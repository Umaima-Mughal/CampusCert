"""AI examiner: turns one prompt into a finished MCQ paper saved in the examiner's own bank.

Flow: 1) plan call (title, subject, topics/difficulty/count)  2) question calls in small batches
3) every question is validated with the SAME rules as file import  4) questions + paper are saved.
"""
import re
from typing import Callable, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.auth.models import User
from app.questions.access import org_scope, same_org
from app.questions.models import ExamPaper, ExamPaperItem, Question, question_hash
from app.questions.parser import ParseResult, _normalize_row

from . import groq_client
from .config import AISettings, get_ai_settings
from .groq_client import GroqError
from .schemas import AIPaperRequest

SYSTEM = ("You are a senior university exam paper setter. You answer with ONE valid JSON object and nothing else. "
          "Write in the same language as the examiner's request.")
DIFFS = ("easy", "medium", "hard")
Chat = Callable[..., dict]


def _chat(messages: list, cfg: AISettings, max_tokens: int) -> dict:
    # looked up at call time so tests can swap groq_client.chat_json
    return groq_client.chat_json(messages, cfg, max_tokens=max_tokens)


# ---------------------------------------------------------------- planning
def _clean(s, limit: int) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()[:limit]


def _diff(value) -> str:
    v = str(value or "").strip().lower()
    return v if v in DIFFS else {"moderate": "medium", "difficult": "hard", "simple": "easy"}.get(v, "medium")


def make_plan(body: AIPaperRequest, cfg: AISettings) -> Tuple[dict, List[Tuple[str, str]]]:
    """Returns (plan dict, slots) where slots is a list of (topic, difficulty), one per question."""
    cap = max(1, cfg.AI_MAX_QUESTIONS)
    fixed = min(body.question_count, cap) if body.question_count else None
    count_rule = (f"The paper must have exactly {fixed} questions." if fixed else
                  f"If the request names a number of questions use it, otherwise use 10. Never more than {cap}.")
    user = (
        f'An examiner wants an exam paper. Their request:\n"""{body.prompt}"""\n\n'
        "Plan the paper. All questions are multiple choice. Reply with JSON exactly like:\n"
        '{"title": "short paper title", "subject": "subject name", '
        '"instructions": "2-3 sentences of instructions for students", "duration_minutes": 30, '
        '"total_questions": 10, "sections": [{"topic": "topic name", "difficulty": "easy", "count": 4}]}\n'
        f"Rules: difficulty is easy, medium or hard. total_questions equals the sum of the section counts. {count_rule} "
        "If the request asks for a difficulty split follow it, otherwise mix easy, medium and hard. "
        "Use real topics of the subject; 2 to 6 sections."
    )
    plan = _chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}], cfg, 1000)

    slots: List[Tuple[str, str]] = []
    subject = _clean(plan.get("subject"), 120) or "General"
    for sec in plan.get("sections") or []:
        if not isinstance(sec, dict):
            continue
        try:
            n = int(sec.get("count") or 0)
        except (TypeError, ValueError):
            continue
        topic = _clean(sec.get("topic"), 160) or subject
        slots += [(topic, _diff(sec.get("difficulty")))] * max(0, min(n, cap))

    try:
        total = int(plan.get("total_questions") or 0)
    except (TypeError, ValueError):
        total = 0
    target = fixed or total or len(slots) or 10
    target = max(1, min(target, cap))
    if not slots:
        slots = [(subject, d) for d in ("easy", "medium", "hard")]
    base, i = list(slots), 0
    while len(slots) < target:                 # pad by cycling the planned sections
        slots.append(base[i % len(base)])
        i += 1
    slots = slots[:target]
    plan["subject"] = subject
    return plan, slots


# ---------------------------------------------------------------- writing questions
_LABEL = re.compile(r"^\(?[A-Da-d][\).:]\s+")


def _strip_labels(raw: dict) -> None:
    opts = [str(raw.get(k) or "") for k in ("option_a", "option_b", "option_c", "option_d")]
    if all(_LABEL.match(o.strip()) for o in opts):
        for k, o in zip(("option_a", "option_b", "option_c", "option_d"), opts):
            raw[k] = _LABEL.sub("", o.strip(), count=1)


def _batch_prompt(subject: str, body: AIPaperRequest, slots: list, already: List[str]) -> str:
    lines = "\n".join(f"{i}. topic: {t} | difficulty: {d}" for i, (t, d) in enumerate(slots, 1))
    avoid = ""
    if already:
        stems = "\n".join(f"- {s[:90]}" for s in already[-40:])
        avoid = f"\nDo NOT repeat or rephrase these questions that are already written:\n{stems}\n"
    return (
        f'Write {len(slots)} multiple-choice exam questions for the subject "{subject}".\n'
        f'The examiner\'s original request, for context:\n"""{body.prompt}"""\n\n'
        f"Write exactly one question for each line, in this order:\n{lines}\n{avoid}\n"
        "Rules: exactly four options, only one is correct, all four are different and believable. "
        "Do not put A) B) labels inside the option text. correct_option is one letter: A, B, C or D, and the correct "
        "answers should be spread over A-D. solution is 1-3 sentences explaining why the answer is right. "
        "easy = recall, medium = apply, hard = multi-step reasoning. Questions must be self-contained and unambiguous.\n"
        'Reply with JSON exactly like: {"questions": [{"topic": "...", "difficulty": "easy", "question": "...", '
        '"option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_option": "B", '
        '"solution": "..."}]}'
    )


def write_questions(body: AIPaperRequest, plan: dict, slots: list, cfg: AISettings) -> Tuple[List[dict], int, List[str]]:
    """Returns (valid rows, skipped count, warnings)."""
    subject = plan["subject"]
    rows: List[dict] = []
    seen, skipped, warnings = set(), 0, []
    target = len(slots)
    batch_size = max(1, cfg.AI_BATCH_SIZE)
    queue = list(slots)
    rounds_left = 2          # extra attempts to top up after bad/missing questions

    while queue:
        batch, queue = queue[:batch_size], queue[batch_size:]
        try:
            data = _chat([{"role": "system", "content": SYSTEM},
                          {"role": "user", "content": _batch_prompt(subject, body, batch, [r["question"] for r in rows])}],
                         cfg, 3500)
        except GroqError as e:
            if not rows:
                raise
            warnings.append(f"Stopped early: {e.message}")
            break
        got = data.get("questions") if isinstance(data, dict) else None
        good = 0
        for i, raw in enumerate(got if isinstance(got, list) else []):
            if not isinstance(raw, dict) or good >= len(batch):
                continue
            slot_topic, slot_diff = batch[min(i, len(batch) - 1)]
            raw = dict(raw)
            _strip_labels(raw)
            raw["subject"] = subject
            raw["topic"] = _clean(raw.get("topic"), 160) or slot_topic
            raw["difficulty"] = raw.get("difficulty") or slot_diff
            res = ParseResult()
            _normalize_row(raw, i + 1, res)
            if not res.rows:
                skipped += 1
                continue
            row = res.rows[0]
            row["topic"] = row["topic"][:160]
            h = question_hash(row["subject"], row["topic"], row["question"])
            if h in seen:
                skipped += 1
                continue
            seen.add(h)
            rows.append(row)
            good += 1
        missing = len(batch) - good
        if missing > 0 and rounds_left > 0 and len(rows) < target:
            rounds_left -= 1
            queue = batch[good:] + queue        # ask again for what is still missing

    if len(rows) < target:
        warnings.append(f"The AI could only write {len(rows)} valid question(s) of the {target} planned.")
    return rows[:target], skipped, warnings


# ---------------------------------------------------------------- saving
def save_paper(db: Session, user: User, body: AIPaperRequest, plan: dict, rows: List[dict]) -> ExamPaper:
    org_id = org_scope(user)
    hashes = {question_hash(r["subject"], r["topic"], r["question"]): r for r in rows}
    mine = (db.query(Question).filter(same_org(Question, org_id), Question.created_by == user.id,
                                      Question.content_hash.in_(list(hashes))).all())
    existing = {q.content_hash: q for q in mine}          # already in this examiner's bank: reuse, never duplicate

    ordered: List[Question] = []
    for h, r in hashes.items():
        q = existing.get(h)
        if q is None:
            q = Question(**r, content_hash=h, organization_id=org_id, created_by=user.id)
            db.add(q)
        ordered.append(q)
    db.flush()

    subject = plan["subject"]
    title = _clean(body.title, 200) or _clean(plan.get("title"), 200) or f"{subject} paper"
    duration = body.duration_minutes
    if not duration:
        try:
            duration = int(plan.get("duration_minutes") or 0)
        except (TypeError, ValueError):
            duration = 0
        duration = duration if 1 <= duration <= 600 else min(600, max(5, len(ordered) * 2))
    paper = ExamPaper(title=title, instructions=_clean(plan.get("instructions"), 2000) or None,
                      duration_minutes=duration, organization_id=org_id)
    db.add(paper)
    db.flush()
    db.add_all(ExamPaperItem(paper_id=paper.id, question_id=q.id, position=n, marks=body.marks_each)
               for n, q in enumerate(ordered, 1))
    db.commit()
    db.refresh(paper)
    return paper


def build_ai_paper(db: Session, user: User, body: AIPaperRequest) -> Tuple[ExamPaper, int, int, List[str], str]:
    cfg = get_ai_settings()
    plan, slots = make_plan(body, cfg)
    rows, skipped, warnings = write_questions(body, plan, slots, cfg)
    if not rows:
        raise GroqError("The AI did not return any usable questions. Try again, or word the prompt more clearly.", 502)
    if body.question_count and body.question_count > cfg.AI_MAX_QUESTIONS:
        warnings.insert(0, f"Papers are limited to {cfg.AI_MAX_QUESTIONS} questions, so that is how many were made.")
    paper = save_paper(db, user, body, plan, rows)
    return paper, len(slots), skipped, warnings, cfg.GROQ_MODEL
