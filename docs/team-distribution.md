# Team Work Distribution

Full detail in the project guide PDF (Section 28). Summary:

| Member | Owns (end-to-end) | Primary folders |
|---|---|---|
| 1 — Core Backend & Auth | FastAPI setup, DB integration, JWT, RBAC, org/user APIs, shared utilities | `backend/app/core`, `backend/app/auth`, `backend/app/organizations`, `database/`, `frontend/src/auth`, `frontend/src/shared`, `frontend/src/api` |
| 2 — Admin Portal | University dashboard, exam creation/configuration, scheduling, candidate management | `backend/app/exams`, `frontend/src/admin` |
| 3 — Question Bank & AI | Question CRUD, subjects/topics/difficulty, bulk import, random selection, AI-assist + approval | `backend/app/questions`, `backend/app/ai`, `frontend/src/questionbank` |
| 4 — Student Portal | Student dashboard, instructions, exam interface, timer, autosave, submission, results view | `backend/app/attempts`, `backend/app/grading`, `frontend/src/student` |
| 5 — Security, Proctoring & Analytics, Examiner Portal | Integrity detection, event logging, freeze/resume/terminate, control room, analytics, audit trail | `backend/app/security`, `backend/app/analytics`, `frontend/src/examiner` |

Audit-trail logging is shared between Member 1 (owns the DB layer) and Member 5
(owns the security/event domain) — coordinate on that specific piece rather than
either person doing it in isolation.

Everyone contributes to testing, documentation, integration, bug fixing,
presentation, and deployment regardless of module ownership.
