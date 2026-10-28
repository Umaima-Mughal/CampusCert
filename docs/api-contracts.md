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
| `POST /api/exams` | Member 2 | implemented | `{ "name": str, "duration_minutes": int, "distribution": { "subject_id": count }, "description"?: str, "instructions"?: str, "starts_at"?: datetime, "ends_at"?: datetime, "passing_score"?: int, "max_attempts"?: int, "shuffle_questions"?: bool, "late_join_minutes"?: int, "organization_id"?: uuid }` | Full exam object (`id`, `status`, `is_active`, schedule, distribution, `candidate_count`, ...) |
| `GET /api/exams` | Member 2 | implemented | optional `?status=` | `[ExamOut]` |
| `GET /api/exams/summary` | Member 2 | implemented | — | `{ "total": int, "by_status": {status: count}, "upcoming": int }` |
| `GET /api/exams/eligible-candidates` | Member 2 | implemented | — | `[{ "id", "full_name", "email", "role", "is_active" }]` |
| `GET /api/exams/{exam_id}` | Member 2 | implemented | — | `ExamOut` |
| `PATCH /api/exams/{exam_id}` | Member 2 | implemented | partial exam fields | `ExamOut` |
| `DELETE /api/exams/{exam_id}` | Member 2 | implemented | drafts only | `204` |
| `POST /api/exams/{exam_id}/schedule` | Member 2 | implemented | `{ "starts_at": datetime, "ends_at": datetime }` | `ExamOut` |
| `POST /api/exams/{exam_id}/activate` | Member 2 | implemented | `{}` | `{ "id", "status": "ACTIVE", "is_active": true }` |
| `POST /api/exams/{exam_id}/deactivate` | Member 2 | implemented | `{}` | `{ "id", "status", "is_active" }` |
| `POST /api/exams/{exam_id}/close` | Member 2 | implemented | `{}` | `{ "id", "status": "CLOSED", "is_active": false }` |
| `POST /api/exams/{exam_id}/archive` | Member 2 | implemented | `{}` | `{ "id", "status": "ARCHIVED", "is_active": false }` |
| `GET /api/exams/{exam_id}/candidates` | Member 2 | implemented | — | `[CandidateOut]` |
| `POST /api/exams/{exam_id}/candidates` | Member 2 | implemented | `{ "user_ids": [uuid] }` | `[CandidateOut]` |
| `DELETE /api/exams/{exam_id}/candidates/{user_id}` | Member 2 | implemented | — | `204` |
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
- **Exam status:** `DRAFT`, `SCHEDULED`, `ACTIVE`, `CLOSED`, `ARCHIVED`
- **Roles (implemented):** `student`, `examiner`, `admin`, `super_admin`
- **Roles:** `PLATFORM_ADMIN`, `ORG_ADMIN`, `EXAMINER`, `CANDIDATE`
- **Event types:** `TAB_SWITCH`, `FULLSCREEN_EXIT`, `COPY_PASTE`, `FACE_NOT_DETECTED`

Admin exam endpoints require a Bearer access token and role `admin` or `super_admin`.
Org admins only see exams in their `organization_id`. Super admins can manage all organizations.
Member 3 should read `distribution` and `shuffle_questions` when selecting papers.
Member 4 should start attempts only for `ACTIVE` exams assigned via `exam_candidates`.
Member 5 can treat `ACTIVE` exams as live sittings for control-room queries.
