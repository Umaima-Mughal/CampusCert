# CampusCert

A secure, transparent SaaS examination platform — semester project.
See `docs/` for the full project guide (architecture, ERD, roadmap, demo script).

## Getting started

**Easiest way — run the whole stack together:**

```bash
git clone <REPO_URL>
cd campuscert
cp .env.example .env      # fill in real values, never commit .env
docker compose up
```

This starts Postgres, the backend, and the frontend together so you can test the
*integrated* product, not just your own module. See `docs/INTEGRATION.md`.

**Running just your own piece without Docker:**

```bash
# backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend
cd ../frontend && npm install && npm run dev
```

---

## Code ownership — who builds what

This is who is responsible for building and maintaining each area — it's about
avoiding two people editing the same files at the same time, not about restricting
who can look at or touch the code. Reviews are handled separately by a rotation,
not by the folder owner — see **Review rotation** below.

| Folder / area | Owner (builds it) | Covers |
|---|---|---|
| `backend/app/core/` | **Member 1** | DB connection, settings, shared utilities, base models — **shared foundation, coordinate before editing** |
| `backend/app/auth/` | **Member 1** | Registration, login, JWT, RBAC |
| `backend/app/organizations/` | **Member 1** | Organization/user APIs |
| `backend/app/exams/` | **Member 2** | Exam creation, configuration, scheduling |
| `backend/app/questions/` | **Member 3** | Question CRUD, subjects/topics/difficulty, bulk CSV/Excel import, random selection |
| `backend/app/ai/` | **Member 3** | AI-assisted question generation + examiner approval workflow |
| `backend/app/attempts/` | **Member 4** | Start/answer/autosave/submit exam-attempt lifecycle |
| `backend/app/grading/` | **Member 4** | Automatic grading, result computation |
| `backend/app/security/` | **Member 5** | Integrity event detection, freeze/resume/terminate |
| `backend/app/analytics/` | **Member 5** | Control room data, analytics, audit-trail queries |
| `database/migrations/` | **Member 1** (primary) | Schema changes — **anyone adding a table/column opens the PR, but Member 1 always reviews** since conflicting migrations are the #1 source of DB merge pain |
| `frontend/src/auth/` | **Member 1** | Login/register screens |
| `frontend/src/admin/` | **Member 2** | University/admin dashboard |
| `frontend/src/questionbank/` | **Member 3** | Question bank UI, bulk import UI, AI-generation review queue |
| `frontend/src/student/` | **Member 4** | Student dashboard, exam-taking interface, results view |
| `frontend/src/examiner/` | **Member 5** | Control room, integrity review UI |
| `frontend/src/shared/` | **Member 1** | Design-system components, layout — **shared, coordinate before editing** |
| `frontend/src/api/` | **Member 1** | API client — **shared; add your module's calls in your own file inside this folder, don't edit someone else's** |
| `docs/` | **whoever owns that topic** | Keep each doc page next to the module it documents |
| `.github/`, root config files | **Member 1** | CI, templates, `.gitignore`, `.env.example` |

### The three rules that actually prevent merge conflicts

1. **Stay inside your folder.** If your task needs a change outside it (e.g., Member 4
   needs a new field on a shared `core` model), open a small PR against that folder and
   ping its owner — don't just edit it inline as part of a bigger feature branch.
2. **Shared files (`core/`, `shared/`, `api/`, migrations) get a heads-up in the team
   chat before you touch them.**
3. **Pull `develop` before starting work, and merge/rebase often** — the longer a
   branch lives untouched, the more likely it drifts into a conflict.

## Merge rules

- **`main` is protected — nobody pushes or merges to it directly.** It only moves
  forward via a PR from `develop`, at the Week 3 and Week 6 milestones (see the
  roadmap in the project guide).
- **`develop` takes PRs from feature branches.** Any teammate *other than the PR's
  author* can review and merge it — there's no fixed reviewer assignment. Whoever's
  free picks it up. The only hard rule is: **you don't approve/merge your own PR.**
- Ping the team chat when your PR is up so someone grabs it — don't let PRs sit
  unreviewed for days.

Full team responsibility breakdown (what each member builds end-to-end, not just
which folder) is in `docs/team-distribution.md`.

## Making integration painless

Folder ownership stops *merge conflicts*. It doesn't stop *interface mismatches* —
the frontend expecting a JSON shape the backend doesn't actually send, which is the
more common way student projects break at integration time. Two things in this repo
exist specifically to prevent that:

- **`docs/api-contracts.md`** — before building a feature that crosses the
  frontend/backend boundary, write down the request/response shape there first and
  get a quick thumbs-up from whoever owns the other side. Costs two minutes, saves
  an integration afternoon.
- **`docker-compose.yml`** — one command (`docker compose up`) runs the database,
  backend, and frontend together, so anyone can pull `develop` and check that the
  *whole* app still works, not just their own module. Run this before every weekly
  merge to `develop`, not just at the Week 6 freeze. See `docs/INTEGRATION.md`.
