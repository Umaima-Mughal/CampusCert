"""
app/grading/grader.py  (Member 4)

The grading rules, as one plain function with no database, so it is easy to unit test.
"""


def grade(questions: list[dict], answers: dict, passing_score: int | None) -> dict:
    """
    questions     : the attempt's layout["questions"] ({"id", "marks", "correct", ...}) in exam order
    answers       : {question_id: "A" | "B" | "C" | "D" | None}
    passing_score : percentage (0-100) needed to pass, or None for "no pass mark"

    A question with no stored correct answer (an old question imported before MCQ support)
    cannot be graded, so it is left out of the total instead of counting against the student.
    """
    total = obtained = correct = incorrect = unanswered = 0
    breakdown = []

    for position, q in enumerate(questions, start=1):
        marks = int(q.get("marks") or 0)
        right = q.get("correct")
        chosen = answers.get(q["id"])
        gradable = right is not None
        awarded = 0

        if gradable:
            total += marks
            if chosen is None:
                unanswered += 1
            elif chosen == right:
                correct += 1
                awarded = marks
            else:
                incorrect += 1
            obtained += awarded

        breakdown.append({
            "question_id": q["id"], "position": position, "marks": marks,
            "selected": chosen, "correct": right, "awarded": awarded, "gradable": gradable,
        })

    percentage = round(obtained / total * 100, 2) if total else 0.0
    passed = None if passing_score is None else percentage >= passing_score
    return {
        "total_marks": total, "obtained_marks": obtained,
        "correct_count": correct, "incorrect_count": incorrect, "unanswered_count": unanswered,
        "percentage": percentage, "passed": passed, "breakdown": breakdown,
    }
