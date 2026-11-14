import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchResult } from "../api/attempts";
import { formatDateTime, percentLabel } from "./studentUtils";

const FILTERS = [
  { id: "all", label: "All" },
  { id: "correct", label: "Correct" },
  { id: "incorrect", label: "Incorrect" },
  { id: "unanswered", label: "Not answered" },
];

function verdict(item) {
  if (!item.gradable) return "ungraded";
  if (!item.selected) return "unanswered";
  return item.selected === item.correct ? "correct" : "incorrect";
}

export default function ResultPage() {
  const { attemptId } = useParams();
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    let cancelled = false;
    fetchResult(attemptId)
      .then((data) => !cancelled && setResult(data))
      .catch((err) => !cancelled && setError(err.message || "Could not load the result."));
    return () => { cancelled = true; };
  }, [attemptId]);

  if (error) {
    return (
      <div className="st-page">
        <div className="st-alert danger">{error}</div>
        <Link className="st-link" to="/student">Back to my exams</Link>
      </div>
    );
  }
  if (!result) return <p className="st-muted">Loading your result...</p>;

  const hasPassMark = result.passed !== null;
  const showCorrect = result.breakdown.some((b) => b.correct);
  const rows = result.breakdown.filter((b) => filter === "all" || verdict(b) === filter);

  return (
    <div className="st-page">
      <Link className="st-link" to="/student">&larr; Back to my exams</Link>

      <div className={`st-result-hero ${hasPassMark ? (result.passed ? "pass" : "fail") : "neutral"}`}>
        <div>
          <p className="st-hero-kicker">{result.exam_name} - attempt #{result.attempt_number}</p>
          <h2>
            {hasPassMark ? (result.passed ? "Congratulations, you passed" : "You did not reach the pass mark") : "Exam submitted"}
          </h2>
          <p className="st-muted">
            Submitted {formatDateTime(result.submitted_at)}
            {hasPassMark ? ` - pass mark ${result.passing_score}%` : ""}
            {result.status === "TERMINATED" ? " - this attempt was ended by the examiner" : ""}
          </p>
        </div>
        <div className="st-score">
          <strong>{percentLabel(result.percentage)}</strong>
          <span>{result.obtained_marks} / {result.total_marks} marks</span>
        </div>
      </div>

      <div className="st-tiles wide">
        <div className="good"><strong>{result.correct_count}</strong><span>Correct</span></div>
        <div className="bad"><strong>{result.incorrect_count}</strong><span>Incorrect</span></div>
        <div><strong>{result.unanswered_count}</strong><span>Not answered</span></div>
        <div><strong>{result.breakdown.length}</strong><span>Questions</span></div>
      </div>

      <h3 className="st-section-title">Review your answers</h3>
      <div className="st-filters" role="tablist">
        {FILTERS.map((f) => (
          <button
            key={f.id}
            type="button"
            role="tab"
            aria-selected={filter === f.id}
            className={`st-filter ${filter === f.id ? "active" : ""}`}
            onClick={() => setFilter(f.id)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {rows.length === 0 && <p className="st-muted">No questions in this view.</p>}
      <div className="st-review">
        {rows.map((item) => {
          const state = verdict(item);
          return (
            <article key={item.question_id} className={`st-review-item ${state}`}>
              <header>
                <strong>Question {item.position}</strong>
                <span className={`st-chip ${state === "correct" ? "ok" : state === "incorrect" ? "danger" : "muted"}`}>
                  {state === "correct" ? "Correct" : state === "incorrect" ? "Incorrect" : state === "unanswered" ? "Not answered" : "Not graded"}
                </span>
                <span className="st-muted">{item.awarded} / {item.marks} marks</span>
              </header>
              <p className="st-question-text">{item.question}</p>
              <ul className="st-review-options">
                {Object.entries(item.options || {}).map(([key, text]) => {
                  const isMine = item.selected === key;
                  const isRight = showCorrect && item.correct === key;
                  return (
                    <li key={key} className={`${isMine ? "mine" : ""} ${isRight ? "right" : ""}`}>
                      <span className="st-option-letter">{key}</span>
                      <span>{text}</span>
                      {isMine && <em>Your answer</em>}
                      {isRight && <em className="right">Correct answer</em>}
                    </li>
                  );
                })}
              </ul>
            </article>
          );
        })}
      </div>
    </div>
  );
}
