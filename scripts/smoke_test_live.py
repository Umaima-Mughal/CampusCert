"""
scripts/smoke_test_live.py

An end-to-end check against the RUNNING backend (real HTTP, real login, real database).
It plays a student through the whole exam, exactly like the browser does, and checks every step:

  login -> dashboard -> instructions -> start -> autosave -> reload (answers still there)
  -> submit -> automatic grading -> result -> privacy (another student cannot see it)

Before you run it:
  1. the backend is running (run_backend.bat)
  2. the demo data exists (python ..\\scripts\\seed_demo_data.py)

Run from the backend folder with the virtual environment active:

    python ..\\scripts\\smoke_test_live.py
    python ..\\scripts\\smoke_test_live.py --wait-expiry     also checks auto-submit when time runs out (takes ~70 s)
    python ..\\scripts\\smoke_test_live.py --url http://localhost:8000

It uses the demo "[DEMO] 1-minute timer test" exam (100 attempts allowed), so it does not use up
the attempts of the other demo exams. Uses only the Python standard library.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_demo_data import DOMAIN, EXAM_NAMES, PASSWORD, QUESTIONS  # noqa: E402

STUDENT1 = f"demo.student1@{DOMAIN}"
STUDENT2 = f"demo.student2@{DOMAIN}"
EXAM_NAME = EXAM_NAMES[1]
CORRECT_BY_TEXT = {q[0]: q[5] for q in QUESTIONS}
WRONG_FOR = {"A": "B", "B": "C", "C": "D", "D": "A"}

failures = []


class Api:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.token = None

    def call(self, method: str, path: str, body=None):
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.base + path, data=data, method=method)
        request.add_header("Content-Type", "application/json")
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode()
                return response.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as err:
            raw = err.read().decode()
            try:
                return err.code, json.loads(raw)
            except ValueError:
                return err.code, raw

    def login(self, email: str, password: str = PASSWORD):
        status, data = self.call("POST", "/api/auth/login", {"email": email, "password": password})
        if status == 200:
            self.token = data["access_token"]
        return status, data


def check(name: str, condition: bool, detail: str = "") -> None:
    detail = " ".join(str(detail).split())[:240]  # one short line, never a wall of text
    print(f"  [{'OK' if condition else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not condition else ""))
    if not condition:
        failures.append(name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--wait-expiry", action="store_true", help="also wait for the 1-minute exam to run out")
    args = parser.parse_args()

    api = Api(args.url)
    print(f"Live smoke test against {args.url}\n")

    print("1. Backend and login")
    try:
        status, health = api.call("GET", "/health")
    except Exception as exc:  # noqa: BLE001
        print(f"  [FAIL] cannot reach the backend: {exc}\n         -> start it first (run_backend.bat)")
        return 1
    check("backend answers /health", status == 200, str(health))
    status, _ = api.login(STUDENT1, "wrong-password")
    check("wrong password is rejected", status in (400, 401, 403), f"got {status}")
    status, data = api.login(STUDENT1)
    check("demo student can log in", status == 200, f"got {status}: {data} -> run seed_demo_data.py first")
    if status != 200:
        return 1
    status, me = api.call("GET", "/api/auth/me")
    check("token works and the role is student", status == 200 and me.get("role") == "student", str(me))

    print("\n2. Dashboard and instructions")
    status, exams = api.call("GET", "/api/attempts/my-exams")
    check("my-exams answers", status == 200 and isinstance(exams, list), f"got {status}: {exams}")
    if status != 200 or not isinstance(exams, list):
        print("\nStopping: the dashboard call failed, so the rest cannot run. Look at the backend window for the error.")
        return 1
    names = [e["name"] for e in exams]
    check("all 3 demo exams are listed", all(n in names for n in EXAM_NAMES), str(names))
    exam = next((e for e in exams if e["name"] == EXAM_NAME), None)
    check("the timer-test exam can be started", bool(exam and (exam["can_start"] or exam["open_attempt_id"])), str(exam))
    if not exam:
        return 1
    upcoming = next((e for e in exams if e["name"] == EXAM_NAMES[2]), None)
    check("the upcoming exam is blocked with a reason", bool(upcoming and not upcoming["can_start"] and upcoming["blocked_reason"]), str(upcoming))
    status, info = api.call("GET", f"/api/attempts/exams/{exam['id']}")
    check("instructions page data", status == 200 and info["question_count"] == 10 and info["duration_minutes"] == 1, str(info))

    print("\n3. Start the exam")
    status, attempt = api.call("POST", "/api/attempts/start", {"exam_id": exam["id"]})
    check("attempt starts", status == 201, f"got {status}: {attempt}")
    if status != 201:
        return 1
    attempt_id = attempt["attempt_id"]
    questions = attempt["questions"]
    check("10 questions, each with 4 options", len(questions) == 10 and all(len(q["options"]) == 4 for q in questions))
    check("the correct answers are NOT sent to the browser", "correct" not in json.dumps(attempt).lower())
    check("a server-side countdown is returned", 0 < attempt["remaining_seconds"] <= 60, str(attempt["remaining_seconds"]))
    status, again = api.call("POST", "/api/attempts/start", {"exam_id": exam["id"]})
    check("starting again resumes the SAME attempt", status == 201 and again["attempt_id"] == attempt_id)

    print("\n4. Answer (autosave)")
    plan = {}  # question id -> chosen key (None = leave unanswered)
    for index, q in enumerate(questions):
        right = CORRECT_BY_TEXT[q["text"]]
        plan[q["id"]] = right if index < 6 else (WRONG_FOR[right] if index < 8 else None)  # 6 right, 2 wrong, 2 blank
    saved_ok = True
    for qid, key in plan.items():
        status, body = api.call("POST", f"/api/attempts/{attempt_id}/answers", {"question_id": qid, "selected_option": key})
        saved_ok = saved_ok and status == 200 and body.get("saved") is True
    check("all 10 answers saved", saved_ok)
    first = questions[0]["id"]
    status, _ = api.call("POST", f"/api/attempts/{attempt_id}/answers", {"question_id": first, "marked_for_review": True})
    check("mark-for-review is saved", status == 200)
    status, _ = api.call("POST", f"/api/attempts/{attempt_id}/answers", {"question_id": first, "selected_option": "Z"})
    check("an invalid option is rejected", status == 422, f"got {status}")
    status, _ = api.call("POST", f"/api/attempts/{attempt_id}/answers", {"question_id": 999999999, "selected_option": "A"})
    check("a question outside this exam is rejected", status == 404, f"got {status}")

    status, reloaded = api.call("GET", f"/api/attempts/{attempt_id}")
    mine = {q["id"]: q["selected"] for q in reloaded["questions"]} if status == 200 else {}
    check("after a reload every answer is still there", mine == plan, str(mine))
    check("the review flag survived the reload", any(q["id"] == first and q["marked_for_review"] for q in reloaded["questions"]))

    print("\n5. Submit and automatic grading")
    status, done = api.call("POST", f"/api/attempts/{attempt_id}/submit")
    check("submit works", status == 200 and done["status"] == "SUBMITTED", f"got {status}: {done}")
    status, done_again = api.call("POST", f"/api/attempts/{attempt_id}/submit")
    check("submitting twice is harmless", status == 200 and done_again["status"] == "SUBMITTED")
    status, late = api.call("POST", f"/api/attempts/{attempt_id}/answers", {"question_id": first, "selected_option": "A"})
    check("answers are refused after submitting", status == 409, f"got {status}")
    status, result = api.call("GET", f"/api/results/{attempt_id}")
    check("result is available", status == 200, f"got {status}: {result}")
    if status == 200:
        check("6 correct, 2 incorrect, 2 not answered",
              (result["correct_count"], result["incorrect_count"], result["unanswered_count"]) == (6, 2, 2), str(result))
        check("score 6 / 10 = 60% and PASSED (pass mark 50%)",
              result["obtained_marks"] == 6 and result["total_marks"] == 10 and result["percentage"] == 60 and result["passed"] is True, str(result))
        check("the review lists all 10 questions", len(result["breakdown"]) == 10)
    status, mine_list = api.call("GET", "/api/results/mine")
    check("the attempt appears in my results", status == 200 and any(r["attempt_id"] == attempt_id for r in mine_list))
    status, finished = api.call("GET", f"/api/attempts/{attempt_id}")
    check("the finished attempt no longer sends questions", status == 200 and finished["status"] == "SUBMITTED" and finished["questions"] == [])

    print("\n6. Privacy")
    other = Api(args.url)
    other.login(STUDENT2)
    status, _ = other.call("GET", f"/api/results/{attempt_id}")
    check("another student cannot read this result", status == 404, f"got {status}")
    status, _ = other.call("GET", f"/api/attempts/{attempt_id}")
    check("another student cannot open this attempt", status == 404, f"got {status}")
    status, _ = other.call("POST", f"/api/attempts/{attempt_id}/answers", {"question_id": first, "selected_option": "A"})
    check("another student cannot change these answers", status == 404, f"got {status}")
    anonymous = Api(args.url)
    status, _ = anonymous.call("GET", "/api/attempts/my-exams")
    check("no login, no access", status in (401, 403), f"got {status}")

    if args.wait_expiry:
        print("\n7. Time runs out (waiting about 70 seconds)")
        status, fresh = api.call("POST", "/api/attempts/start", {"exam_id": exam["id"]})
        check("a new attempt starts", status == 201, f"got {status}: {fresh}")
        if status == 201:
            fid = fresh["attempt_id"]
            q0 = fresh["questions"][0]
            api.call("POST", f"/api/attempts/{fid}/answers", {"question_id": q0["id"], "selected_option": CORRECT_BY_TEXT[q0["text"]]})
            print("         answered 1 question, now doing nothing ...")
            time.sleep(fresh["remaining_seconds"] + 8)
            status, after = api.call("GET", f"/api/attempts/{fid}")
            check("the exam was submitted automatically", status == 200 and after["status"] == "SUBMITTED", str(after))
            status, res = api.call("GET", f"/api/results/{fid}")
            check("and graded automatically (1 correct, 9 not answered)",
                  status == 200 and res["correct_count"] == 1 and res["unanswered_count"] == 9, str(res))

    print()
    if failures:
        print(f"RESULT: {len(failures)} check(s) FAILED:")
        for name in failures:
            print(f"   - {name}")
        return 1
    print("RESULT: everything works. The whole student flow is correct from login to graded result.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
