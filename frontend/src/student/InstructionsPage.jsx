import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { fetchExamInstructions, startAttempt } from "../api/attempts";
import { formatDateTime } from "./studentUtils";

const RULES = [
  "The timer starts the moment you press Start and keeps running even if you close the page or lose your connection.",
  "Every answer is saved automatically as soon as you choose it. You do not need a save button.",
  "You can move between questions, change answers and mark questions for review at any time.",
  "When the time ends, your exam is submitted and graded automatically with the answers saved so far.",
  "If you reload the page or come back later, you continue from where you stopped, with the time that is left.",
  "Do not share your screen, open other exams or let anyone else answer for you. Suspicious activity may pause or end your exam.",
];

export default function InstructionsPage() {
  const { examId } = useParams();
  const navigate = useNavigate();
  const [info, setInfo] = useState(null);
  const [error, setError] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchExamInstructions(examId)
      .then((data) => !cancelled && setInfo(data))
      .catch((err) => !cancelled && setError(err.message || "Could not load this exam."));
    return () => { cancelled = true; };
  }, [examId]);

  async function handleStart() {
    setStarting(true);
    setError("");
    try {
      const attempt = await startAttempt(examId);
      navigate(`/student/attempt/${attempt.attempt_id}`, { replace: true });
    } catch (err) {
      setError(err.message || "Could not start the exam.");
      setStarting(false);
    }
  }

  if (!info && !error) return <p className="st-muted">Loading instructions...</p>;
  if (!info) {
    return (
      <div className="st-page">
        <div className="st-alert danger">{error}</div>
        <Link className="st-link" to="/student">Back to my exams</Link>
      </div>
    );
  }

  return (
    <div className="st-page narrow">
      <Link className="st-link" to="/student">&larr; Back to my exams</Link>
      <div className="st-panel">
        <h2>{info.name}</h2>
        {info.description && <p className="st-muted">{info.description}</p>}

        <dl className="st-facts big">
          <div><dt>Duration</dt><dd>{info.duration_minutes} minutes</dd></div>
          <div><dt>Questions</dt><dd>{info.question_count}</dd></div>
          <div><dt>Pass mark</dt><dd>{info.passing_score === null ? "None" : `${info.passing_score}%`}</dd></div>
          <div><dt>Attempts allowed</dt><dd>{info.max_attempts}</dd></div>
          {info.ends_at && <div><dt>Must start before</dt><dd>{formatDateTime(info.ends_at)}</dd></div>}
        </dl>

        {info.instructions && (
          <>
            <h3 className="st-section-title">Instructions from your examiner</h3>
            <div className="st-instructions-text">{info.instructions}</div>
          </>
        )}

        <h3 className="st-section-title">Exam rules</h3>
        <ul className="st-rules">
          {RULES.map((rule) => <li key={rule}>{rule}</li>)}
        </ul>

        {error && <div className="st-alert danger">{error}</div>}

        <label className="st-check">
          <input type="checkbox" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} />
          <span>I have read the instructions and I am ready to begin. I understand the timer cannot be paused.</span>
        </label>

        <div className="st-actions">
          <Link className="st-btn secondary" to="/student">Cancel</Link>
          <button type="button" className="st-btn primary" disabled={!agreed || starting} onClick={handleStart}>
            {starting ? "Starting..." : "Start exam"}
          </button>
        </div>
      </div>
    </div>
  );
}
