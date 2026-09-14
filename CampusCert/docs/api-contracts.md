# API Contracts

Fill this in *before* building a feature that crosses the frontend/backend
boundary — it's the cheapest way to avoid integration surprises. Update the
status as you go. Doesn't need to be fancy; a clear example request/response is
enough.

| Endpoint | Owner | Status | Request shape | Response shape |
|---|---|---|---|---|
| `POST /auth/login` | Member 1 | draft | `{ "email": str, "password": str }` | `{ "access_token": str, "role": str }` |
| `POST /auth/register` | Member 1 | draft | `{ "email": str, "password": str, "name": str }` | `{ "id": str, "email": str }` |
| `POST /questions/bulk-import` | Member 3 | draft | multipart CSV/XLSX file | `{ "imported": int, "errors": [ { "row": int, "reason": str } ] }` |
| `POST /exams` | Member 2 | draft | `{ "name": str, "duration_minutes": int, "distribution": { "subject_id": count } }` | `{ "id": str, "status": "DRAFT" }` |
| `POST /attempts/{id}/answers` | Member 4 | draft | `{ "question_id": str, "selected_option_id": str }` | `{ "saved": true }` |
| `POST /attempts/{id}/submit` | Member 4 | draft | `{}` | `{ "status": "SUBMITTED" }` |
| `POST /events` | Member 5 | draft | `{ "attempt_id": str, "type": "TAB_SWITCH" \| "FULLSCREEN_EXIT" \| ... }` | `{ "attempt_status": "FROZEN" }` |
| `POST /attempts/{id}/resume` | Member 5 | draft | `{}` | `{ "attempt_status": "ACTIVE" }` |
| `POST /ai/questions/generate` | Member 3 | draft | `{ "subject": str, "topic": str, "difficulty": str, "count": int }` | `{ "drafts": [ { "stem": str, "options": [str], "correct_index": int } ] }` |
| `GET /results/{attempt_id}` | Member 4 / 5 | draft | — | `{ "score": num, "breakdown": {...}, "audit_trail": [...] }` |

## Shared enums / constants

Keep these in one place (`backend/app/core/` on the backend, mirrored as a
constants file in `frontend/src/shared/`) instead of each module hardcoding its
own strings.

- **Attempt status:** `NOT_STARTED`, `ACTIVE`, `FROZEN`, `SUBMITTED`, `TERMINATED`
- **Roles:** `PLATFORM_ADMIN`, `ORG_ADMIN`, `EXAMINER`, `CANDIDATE`
- **Event types:** `TAB_SWITCH`, `FULLSCREEN_EXIT`, `COPY_PASTE`, `FACE_NOT_DETECTED`
