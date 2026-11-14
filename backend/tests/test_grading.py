"""Grading rules (Member 4). Pure function, no database."""
from app.grading.grader import grade


def qs(*rows):
    return [{"id": i, "marks": m, "correct": c} for i, m, c in rows]


def test_counts_and_percentage():
    questions = qs((1, 1, "A"), (2, 1, "B"), (3, 2, "C"), (4, 1, "D"))
    answers = {1: "A", 2: "A", 3: "C", 4: None}
    r = grade(questions, answers, passing_score=50)
    assert (r["correct_count"], r["incorrect_count"], r["unanswered_count"]) == (2, 1, 1)
    assert (r["obtained_marks"], r["total_marks"]) == (3, 5)
    assert r["percentage"] == 60.0
    assert r["passed"] is True


def test_missing_answer_counts_as_unanswered():
    r = grade(qs((1, 1, "A")), {}, passing_score=None)
    assert r["unanswered_count"] == 1 and r["obtained_marks"] == 0


def test_no_passing_score_means_passed_is_none():
    assert grade(qs((1, 1, "A")), {1: "A"}, passing_score=None)["passed"] is None


def test_fail_below_pass_mark_and_pass_exactly_on_it():
    questions = qs((1, 1, "A"), (2, 1, "A"))
    assert grade(questions, {1: "A", 2: "B"}, 60)["passed"] is False
    assert grade(questions, {1: "A", 2: "B"}, 50)["passed"] is True


def test_question_without_correct_answer_is_not_counted_against_student():
    questions = qs((1, 1, "A"), (2, 1, None))
    r = grade(questions, {1: "A", 2: "B"}, 100)
    assert r["total_marks"] == 1 and r["percentage"] == 100.0
    assert r["breakdown"][1]["gradable"] is False


def test_empty_exam_does_not_divide_by_zero():
    r = grade([], {}, 50)
    assert r["percentage"] == 0.0 and r["passed"] is False


def test_marks_per_question_are_respected():
    r = grade(qs((1, 5, "A"), (2, 1, "A")), {1: "A", 2: "B"}, None)
    assert r["obtained_marks"] == 5 and r["total_marks"] == 6
