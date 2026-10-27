# Member 4: Student Portal (attempts, timer, autosave, grading, results)

## What a student can do
1. **Dashboard** (`/student`): sees the exams assigned to them, their status, attempts used and past results.
2. **Instructions** (`/student/exam/:examId`): reads the exam rules and the examiner's instructions, ticks "I am ready", then starts.
3. **Exam screen** (`/student/attempt/:attemptId`): countdown timer, next/previous, question palette, mark for review, clear answer, autosave indicator, submit confirmation.
4. **Result** (`/student/result/:attemptId`): score, pass/fail, counts, and a filterable review of every question.

## How it works
| Topic | Behaviour |
|---|---|
| Start rules | Exam must be `ACTIVE`, student assigned, inside its time window, attempts left, and have a paper. Otherwise a clear message is shown. |
| Resume | Starting again (or reloading) returns the open attempt with the time that is left. |
| Timer | The server owns the clock (`remaining_seconds`). The browser counts down and re-syncs every 20 s. At zero the exam is submitted automatically. If the browser is closed, the server grades the attempt the next time it is opened. |
| Autosave | Each click is sent immediately. Failed saves stay in a queue and are retried every 3 s until they work. Submitting first waits for the queue to empty. |
| Frozen | `FROZEN` attempts reject answers and show a "paused" screen. The screen checks every 5 s and continues when it is `ACTIVE` again. |
| Snapshot | At start, each attempt stores its own question order, option order and correct answers, so later edits to the bank do not change it. |
| Grading | Correct = marks of that question. Wrong and unanswered = 0. Questions with no stored correct answer are left out of the total. Percentage is compared with the exam's `passing_score`. |
| Audit trail | Every save is appended to `answer_log` with a timestamp. |
| Correct answers | Never sent while the exam is running. The result page shows them if `SHOW_CORRECT_ANSWERS` is `True` in `backend/app/attempts/constants.py`. |

## Files
```
database/migrations/versions/0008_student_attempts.py   tables: exam_attempts, candidate_answers, answer_log, results
backend/app/attempts/    models, schemas, services (all rules), routes, constants
backend/app/grading/     grader (pure function), models, routes (/api/results)
backend/tests/           test_grading.py, test_attempts_flow.py, test_attempts_api.py, test_demo_seed.py
frontend/src/api/attempts.js
frontend/src/student/    StudentRoutes, StudentLayout, StudentGuard, StudentDashboard,
                         InstructionsPage, ExamPage, ResultPage, studentUtils.js, student.css
frontend/src/__tests__/  studentUtils.test.js, examScreen.test.jsx, studentPages.test.jsx
scripts/                 check_database.py, seed_demo_data.py, smoke_test_live.py
*.bat (project root)     setup_windows, run_migrations, run_backend, run_frontend, run_all_checks, live_check, ...
docs/RUN_GUIDE.md        complete run and verification guide
```
Shared files touched: `backend/app/main.py` (2 routers), `database/migrations/env.py` (2 model imports), `frontend/src/App.jsx` (`/student/*` route and student redirects), `frontend/package.json` (two dev-only test libraries: jsdom, @testing-library/react), `.env.example` (correct setting names), `docs/api-contracts.md`.

## Try it
1. `alembic upgrade head` (project root), start the backend and the frontend.
2. As admin: create an exam, attach a question paper, add a student under candidates, set the exam to **ACTIVE**.
3. Log in as that student: the dashboard shows the exam. Start it, answer a few questions, refresh the page (answers and time are kept), then submit and open the result.
4. To see the timer end by itself, create an exam with a 1 minute duration.

## Tests (full details and expected output: docs/RUN_GUIDE.md)
- Everything that needs no running app: `run_all_checks.bat` (database check, 62 backend tests, 30 frontend tests, build).
- The whole student flow against the running backend: `live_check.bat` (add `--wait-expiry` to also test the automatic submit).
