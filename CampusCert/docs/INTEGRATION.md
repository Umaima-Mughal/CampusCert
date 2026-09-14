# Integration Guide

The point of this file: make sure combining five people's work at the end is
boring, not a crisis. Two habits do almost all the work.

## 1. Run the whole stack together, every week — not just at Week 6

```bash
docker compose up --build
```

This brings up Postgres, the backend, and the frontend as one running product.
Do this **every time you merge into `develop`**, not just before the final demo.
If something breaks when your branch meets everyone else's, you want to find out
on a Tuesday in Week 3, not the night before the presentation.

A simple weekly habit that works well for a 5-person team: pick one time each
week (e.g. Friday evening) where everyone has merged their finished work into
`develop`, and one person runs `docker compose up` and walks through the full
demo flow (Section 32 of the project guide) end-to-end. Log anything that breaks
as a GitHub issue immediately.

## 2. Agree on the interface before building both sides of it

Most "integration problems" in student projects aren't merge conflicts — they're
the frontend expecting `{ "score": 85 }` while the backend sends
`{ "result": { "percentage": 85 } }`. Folder ownership can't catch this because
both sides are "correct" in isolation.

Fix: before a feature that crosses the frontend/backend boundary gets built,
whoever's building the backend side writes the request/response shape into
`docs/api-contracts.md` first, and whoever's building the frontend side gives it
a quick look before either of you starts coding. Two minutes now beats a
half-day of debugging why the exam score never shows up in the UI.

## 3. Keep shared things actually shared

- Anything both frontend and backend need to agree on (status enums like
  `FROZEN`/`ACTIVE`/`SUBMITTED`, role names, error formats) goes in one place —
  document it in `docs/api-contracts.md` rather than each module inventing its
  own version.
- If you change a shared model in `backend/app/core/` or a shared component in
  `frontend/src/shared/`, say so in the team chat the same day — someone else's
  in-progress branch may depend on the old shape.

## 4. What "done" means for a feature before it merges to develop

- [ ] Works against the real database, not just made-up test data
- [ ] Matches the agreed shape in `docs/api-contracts.md` (if applicable)
- [ ] Runs cleanly via `docker compose up` alongside everyone else's current code
- [ ] No console errors / unhandled exceptions in the happy path
