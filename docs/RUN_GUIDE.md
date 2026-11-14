# CampusCert: complete run and verification guide (Windows + VS Code)

This guide takes you from the unzipped folder to a running backend, a running frontend, a correct
database, and a full set of passing checks. Follow the parts in order. Every command can be copied
as written. Keep the project in a path you can type, for example
`E:\5th Semester\EC\Project\hello\repo-clean`.

**Short version** (details below): put your `backend\.env` in place, then run
`setup_windows.bat`, `run_all_checks.bat`, `seed_demo.bat`, `run_backend.bat`,
`run_frontend.bat`, `live_check.bat`.

---

## Part 1. What you need installed

| Tool | Version | How to check (in the VS Code terminal) |
|---|---|---|
| Python | 3.11 or newer (3.13 works) | `python --version` |
| Node.js (includes npm) | 18 or newer | `node --version` and `npm --version` |
| VS Code | any recent | Terminal menu opens a terminal inside the project |
| Internet | needed | your database (Supabase) is online |

If `node` or `python` is "not recognized", install it, **close VS Code completely**, and open it again.
If PowerShell refuses to run scripts, run this once:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Part 2. Get the project in place

1. Unzip `repo-clean-with-student-portal.zip`. You get a folder called `repo-clean`.
2. In VS Code: **File > Open Folder** and choose that `repo-clean` folder.
3. The zip does **not** contain your secrets, so create `backend\.env` (Part 3).
   If you already have a working `backend\.env` from your old copy, just copy that file to
   `repo-clean\backend\.env` and continue with Part 3, step 2.

## Part 3. The `backend\.env` file (your database and login secret)

1. Copy `.env.example` (in the project root) to `backend\.env`.
2. Open `backend\.env` and fill it in. The names must be exactly these:

```
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/postgres
JWT_SECRET_KEY=any-long-random-text
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

* `DATABASE_URL`: from Supabase, Project settings > Database > Connection string > URI.
  If your password contains special characters, encode them: `@` becomes `%40`, `#` becomes `%23`,
  `/` becomes `%2F`.
* `JWT_SECRET_KEY`: make one with `python -c "import secrets; print(secrets.token_hex(32))"`.
  **The name is `JWT_SECRET_KEY`.** If an old `.env` says `JWT_SECRET=` the backend ignores it and
  uses an insecure default, so rename that line.
* Never send `.env` to anyone and never commit it to GitHub. It contains your database password.
  If it was ever shared, reset the database password in Supabase and update `DATABASE_URL`.

## Part 4. One-time setup

**Easy way:** double-click `setup_windows.bat` (or type `setup_windows.bat` in the VS Code terminal).
It creates the Python environment, installs backend and frontend packages, and runs the database
check. A `venv` folder copied from another computer is detected and rebuilt automatically.

**Manual way** (same result), in the VS Code terminal opened at `repo-clean`:

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt pytest
cd ..\frontend
npm install
cd ..
```

After `venv\Scripts\activate` your prompt starts with `(venv)`. That means the right Python is active.
(If a `venv` folder already exists and gives errors like "Fatal error in launcher", delete it with
`rmdir /s /q backend\venv` and create it again as above.)

## Part 5. The database tables

### What a correct database contains

Twelve tables plus Alembic's own version table:

| Table | Owner | Holds |
|---|---|---|
| `roles`, `organizations`, `users` | Member 1 | accounts and the roles student / examiner / admin / super_admin |
| `exams`, `exam_candidates` | Member 2 | exams and which students are assigned |
| `questions`, `exam_papers`, `exam_paper_items` | Member 3 | question bank and the papers built from it |
| **`exam_attempts`** | **Member 4** | one row per student sitting; stores the frozen copy of the questions, the end time and the status |
| **`candidate_answers`** | **Member 4** | the student's current answer per question (autosave overwrites it) |
| **`answer_log`** | **Member 4** | every save ever made, with a timestamp (the audit trail) |
| **`results`** | **Member 4** | the graded result of each attempt, with a per-question breakdown |
| `alembic_version` | Alembic | the number of the last migration that was applied |

The tables are created by migrations `0001` to `0008` in `database\migrations\versions`.
The database is "correct" when `alembic_version` says `0008_student_attempts`.

### Create or update the tables

From the project root (`repo-clean`), with the venv active:

```
alembic upgrade head
alembic current
```

or double-click `run_migrations.bat`. Expected result: `0008_student_attempts (head)`.
Running it again is harmless. A fresh, empty database gets all tables from scratch (verified on an
empty PostgreSQL 16 while preparing this guide: all nine migrations applied in order). A database that
is already on `0007` gets only the four new Member 4 tables, and nothing existing is changed.

> Always run `alembic` from `repo-clean` (the folder that contains `alembic.ini`), and `uvicorn`
> and `pytest` from `repo-clean\backend`.

### Check that the database is correct

```
cd backend
python ..\scripts\check_database.py
```

or double-click `check_database.bat`. It only reads, it changes nothing. It checks the connection,
the migration number, every table and every column the code expects, and the default roles. The last
line must be:

```
RESULT: the database is correct. All tables and columns the code needs are there.
```

Any `[FAIL]` line tells you what is wrong and what to run to fix it.

## Part 6. Demo data (optional but recommended for testing)

So you do not have to build an exam by hand:

```
cd backend
python ..\scripts\seed_demo_data.py
```

(or `seed_demo.bat`). It shows which database it will write to and waits until you type `YES`.
It creates the organization "CampusCert Demo University", four users (all with password
`Demo@12345`), 10 networking questions, one paper and three exams with both students assigned:

| Login | Role |
|---|---|
| `demo.student1@campuscert-demo.edu` | student |
| `demo.student2@campuscert-demo.edu` | student |
| `demo.examiner@campuscert-demo.edu` | examiner |
| `demo.admin@campuscert-demo.edu` | admin |

| Exam | Purpose |
|---|---|
| [DEMO] Computer Networks Quiz | 15 minutes, 3 attempts: the normal exam to walk through |
| [DEMO] 1-minute timer test | leave it running to watch the exam submit and grade itself |
| [DEMO] Upcoming exam | opens tomorrow, so students see it as "Upcoming" and cannot start it |

Running it twice does not create duplicates. **If your `.env` points at the team's shared database,
the demo rows are visible to everyone** until you delete them:
`python ..\scripts\seed_demo_data.py --remove` (or `remove_demo.bat`). That removes exactly the demo
rows, including attempts and results made with them.

## Part 7. Run the backend

```
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

or double-click `run_backend.bat`. Leave this window open. Then open:

* http://localhost:8000/health shows `{"status":"ok","app":"CampusCert"}`
* http://localhost:8000/docs lists every endpoint, including the `attempts` and `results` sections

## Part 8. Run the frontend

In a **second** terminal:

```
cd frontend
npm run dev
```

or double-click `run_frontend.bat`. Open http://localhost:5173. The frontend talks to the backend at
`http://localhost:8000` (set in `frontend\.env.local` as `VITE_API_URL`; if that file is missing the
default is the same address).

## Part 9. Try it by hand (5 minutes)

Log in as `demo.student1@campuscert-demo.edu` / `Demo@12345`. You land on `/student`.

| Step | What you should see |
|---|---|
| Dashboard | three exam cards: Quiz = Open, Timer test = Open, Upcoming exam = Upcoming with "This exam is not open." |
| Press **Start exam** on the Quiz | the instructions page; **Start exam** stays disabled until you tick the checkbox |
| Start | the exam screen: countdown near 15:00, Question 1 of 10, option buttons, a question palette on the right |
| Click an option | it highlights; the top bar says "Saving..." then "All answers saved" |
| **Mark for review**, then **Next** | the palette number turns amber |
| **Reload the page** (F5) | the same attempt, your answers still selected, the timer continues from the server time (browser asks to confirm leaving: that is intentional) |
| **Submit exam** | a confirmation with counts answered / not answered / for review |
| **Yes, submit** | the result page: score, percentage, pass or fail, and a review of every question |
| Back on the dashboard | the Quiz now shows the attempt count 1 / 3 and a "My results" table |
| Timer test exam | start it and wait one minute without touching it: the screen shows "Time is up", submits by itself and opens the graded result |
| Turn off Wi-Fi while answering | the bar says "No connection - retrying automatically"; turn it back on and it says saved |

## Part 10. The automatic checks

### 10.1 Everything that does not need the running app

Double-click `run_all_checks.bat`, or in the terminal at `repo-clean`:

```
cd backend
python ..\scripts\check_database.py
python -m pytest -q
cd ..\frontend
npm test
npm run build
```

Expected: database check ends with `RESULT: the database is correct`, `62 passed`, `30 passed (5 files)`,
and the build ends with `built in ...`.
(Deprecation warnings from the libraries are normal. Failures are not.)

### 10.2 The whole student flow on the running app

With the backend running (Part 7) and the demo data present (Part 6):

```
cd backend
python ..\scripts\smoke_test_live.py
python ..\scripts\smoke_test_live.py --wait-expiry
```

or `live_check.bat` and `live_check.bat --wait-expiry`. It logs in as a demo student over real HTTP and
plays the whole exam: wrong password rejected, dashboard, instructions, start, answer, reload, submit,
grading (6 right, 2 wrong, 2 blank = 60% passed), results, privacy against a second student and against
anonymous access. With `--wait-expiry` it also leaves an exam running until the clock ends and checks
that the server submitted and graded it. Expected last line:

```
RESULT: everything works. The whole student flow is correct from login to graded result.
```

(36 checks with `--wait-expiry`, 33 without.) It uses the 1-minute demo exam, which allows 100
attempts, so running it often does not use up the attempts of the other exams.

### 10.3 What every automated test covers

**Backend, 62 tests in `backend\tests`**

| File | Tests | What it proves |
|---|---|---|
| `test_grading.py` | 7 | marks, correct / incorrect / unanswered counts, percentage, pass mark, no pass mark, questions without a stored answer, empty exam |
| `test_attempts_flow.py` | 14 | start > answer > submit > grade; autosave overwrites but logs every save; clear answer and review flag; starting twice resumes; attempt limit; only assigned students; exam must be active and inside its window; nobody can read or change another student's attempt; invalid option or question rejected; time up submits and grades automatically; frozen attempt rejects answers; double submit is harmless; editing a question mid-exam does not change the student's grade; dashboard list |
| `test_attempts_api.py` | 2 | the whole flow through the real HTTP routes with JSON shapes; `main.py` registers the student routes |
| `test_demo_seed.py` | 4 | the demo script creates the setup, is repeatable, a demo student can really take the demo exam, remove deletes everything |
| `test_exam_paper_rules.py` | 21 | Member 3: paper building rules |
| `test_exams.py` | 6 | Member 2: exams |
| `test_private_question_banks.py` | 7 | Member 3: private question banks |
| `test_placeholder.py` | 1 | the test setup itself |

**Frontend, 30 tests in `frontend\src\__tests__`**

| File | Tests | What it proves |
|---|---|---|
| `examScreen.test.jsx` | 9 | clock and restored answers, autosave on click, offline retry keeps the answer, review flag and clear, submit confirmation then result, automatic submit at zero, paused screen blocks answers, finished attempt goes to the result, load error shown |
| `studentPages.test.jsx` | 9 | dashboard buttons (start / resume / view result / blocked reason / empty state), instructions page agreement gate and error, result score, filters and hidden answers |
| `studentUtils.test.js` | 8 | clock format, timer colours, UTC time reading, palette states, counts, network vs server errors, badges |
| `examUtils.test.js`, `placeholder.test.js` | 4 | existing admin helpers |

The frontend tests replace the backend with mocks, so they need no server. The live check (10.2) and
the backend tests together cover the other direction.

## Part 11. Troubleshooting

| What you see | Cause and fix |
|---|---|
| `Can't locate revision identified by '0007_...'` or `'0008_...'` | The database is newer than your code. Use the project from this zip (it contains migrations up to `0008`). |
| `Fatal error in launcher: Unable to create process using ...venv...` | The `venv` was copied from another computer. `rmdir /s /q backend\venv`, then run `setup_windows.bat`. |
| `No config file 'alembic.ini' found` | You are in the wrong folder. `cd` to `repo-clean` first. |
| `No module named 'app'` when starting uvicorn | You are not inside `repo-clean\backend`, or the venv is not active (prompt must start with `(venv)`). |
| `'npm' is not recognized` | Install Node.js LTS, restart VS Code. |
| `could not connect` / timeout | Check internet and `DATABASE_URL`; open the Supabase dashboard (free projects pause after inactivity). Run `check_database.bat` to see the exact message. |
| Login works but you are logged out at once / tokens rejected | `JWT_SECRET_KEY` is misspelled in `.env` (it must not be `JWT_SECRET`). Restart the backend after editing `.env`. |
| `/docs` has no `attempts` section | The 5 student lines are missing at the bottom of `backend\app\main.py` (they are included in this zip). The test `test_student_routes_are_registered_in_main_app` says exactly this when it fails. |
| Student dashboard is empty | The student is not assigned to an exam. Run `seed_demo.bat`, or in the admin portal add the student as a candidate. |
| "This exam is not open." | The exam status must be ACTIVE, with a paper attached, inside its time window. |
| "no question paper" | Attach a paper to the exam in the admin portal. |
| Frontend loads but every action fails | The backend is not running, or you opened a different address than `http://localhost:5173`. |
| Exam times look 5 hours off in the admin screens | The student portal reads server times as UTC and shows local time. If an admin screen shows a different time, that is the admin screen, not the exam clock (the exam clock comes from the server). |
| `live_check` says "cannot reach the backend" | Start `run_backend.bat` first. |
| `live_check` says login failed | Run `seed_demo.bat` first. |
| pytest says `ModuleNotFoundError` | The venv is not active, or run `pip install -r requirements.txt pytest` again. |

## Part 12. Good to know

* **Students cannot cheat the clock.** The end time is stored on the server. Reloading, changing the
  computer clock or closing the browser does not add time. If the browser is closed, the exam is
  submitted and graded the next time anyone opens it after the end time.
* **Correct answers never reach the browser during an exam.** The result page shows them afterwards.
  To hide them from students, set `SHOW_CORRECT_ANSWERS = False` in `backend\app\attempts\constants.py`.
* **Each attempt keeps its own copy of the questions**, so an examiner editing a question during an
  exam does not change what a student sees or how they are graded.
* **Member 5 hooks:** setting an attempt's status to `FROZEN` pauses answering and shows the paused screen;
  `finalize_attempt(db, attempt, "TERMINATED")` in `backend\app\attempts\services.py` ends and grades one.
* **Shared database:** the same Supabase database is probably used by the whole team. Run
  `alembic upgrade head` only when the team knows, and remove demo data when you are done presenting.
* **What was tested while preparing this guide:** all migrations on an empty PostgreSQL 16 database; the
  database checker against a correct, an outdated and an unreachable database; the demo script (add,
  repeat, remove, with real foreign keys); the complete live flow including the one-minute timeout against
  a running backend on that database; all 62 backend and 30 frontend tests; the production build. It was
  not run against your own Supabase project or in a real browser here, which is why Part 9 is a short
  hand-check for you.
