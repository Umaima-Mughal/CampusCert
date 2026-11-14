"""Random question selection with the teacher's filters."""
import random

from fastapi import HTTPException
from sqlalchemy import func

from .models import Question

DIFFICULTIES = ("easy", "medium", "hard")


def select_random(db, req, base_query=None):
    """Returns (items, requested, available, shortfall). `req` is a RandomRequest.
    `base_query` limits the pool (the router passes the user's organization's questions)."""
    if req.mix is not None and req.difficulty is not None:
        raise HTTPException(422, "Choose either one difficulty or a mix, not both.")
    if req.mix is None and req.count is None:
        raise HTTPException(422, "Say how many questions you want, or give a mix.")

    pool = base_query if base_query is not None else db.query(Question)
    if req.subject:
        pool = pool.filter(Question.subject == req.subject)
    if req.topics:
        pool = pool.filter(Question.topic.in_(req.topics))
    if req.exclude_ids:
        pool = pool.filter(~Question.id.in_(req.exclude_ids))

    def pick(query, n):
        return query.order_by(func.random()).limit(n).all()

    shortfall, items = {}, []
    if req.mix is not None:
        if any(k not in DIFFICULTIES for k in req.mix) or any(v < 0 for v in req.mix.values()):
            raise HTTPException(422, "Mix must use easy, medium and hard with numbers of 0 or more.")
        requested = sum(req.mix.values())
        if requested < 1 or requested > 200:
            raise HTTPException(422, "Ask for between 1 and 200 questions in total.")
        wanted = [d for d, n in req.mix.items() if n > 0]
        available = pool.filter(Question.difficulty.in_(wanted)).count()
        for d in wanted:
            got = pick(pool.filter(Question.difficulty == d), req.mix[d])
            items.extend(got)
            if len(got) < req.mix[d]:
                shortfall[d] = req.mix[d] - len(got)
        random.shuffle(items)
    else:
        requested = req.count
        if req.difficulty:
            pool = pool.filter(Question.difficulty == req.difficulty)
        available = pool.count()
        items = pick(pool, requested)
        if len(items) < requested:
            shortfall["total"] = requested - len(items)
    return items, requested, available, shortfall
