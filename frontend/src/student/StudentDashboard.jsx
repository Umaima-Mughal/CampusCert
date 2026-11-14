import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { fetchMyExams, fetchMyResults } from "../api/attempts";
import { useAuth } from "../auth/AuthContext";
import { examBadge, formatDateTime, percentLabel } from "./studentUtils";

function ExamCard({ exam }) {
  const navigate = useNavigate();
  const badge = examBadge(exam);
  const finished = exam.last_attempt_id && ["SUBMITTED", "TERMINATED"].includes(exam.last_attempt_status);

  let action;
  if (exam.open_attempt_id) {
    action = (
      <button type="button" className="st-btn primary" onClick={() => navigate(`/student/attempt/${exam.open_attempt_id}`)}>
        Resume exam
      </button>
    );
  } else if (exam.can_start) {
    action = (
      <button type="button" className="st-btn primary" onClick={() => navigate(`/student/exam/${exam.id}`)}>
        {exam.attempts_used > 0 ? "Start another attempt" : "Start exam"}
      </button>
    );
  } else if (finished) {
    action = (
      <button type="button" className="st-btn secondary" onClick={() => navigate(`/student/result/${exam.last_attempt_id}`)}>
        View result
      </button>
    );
  } else {
    action = <button type="button" className="st-btn secondary" disabled>Not available</button>;
  }

  return (
    <article className="st-card">
      <div className="st-card-head">
        <h3>{exam.name}</h3>
        <span className={`st-chip ${badge.tone}`}>{badge.label}</span>
      </div>
      {exam.description && <p className="st-card-desc">{exam.description}</p>}
      <dl className="st-facts">
        <div><dt>Duration</dt><dd>{exam.duration_minutes} min</dd></div>
        <div><dt>Attempts</dt><dd>{exam.attempts_used} / {exam.max_attempts}</dd></div>
        <div><dt>Opens</dt><dd>{exam.starts_at ? formatDateTime(exam.starts_at) : "Any time"}</dd></div>
        <div><dt>Closes</dt><dd>{exam.ends_at ? formatDateTime(exam.ends_at) : "No deadline"}</dd></div>
      </dl>
      {!exam.can_start && !exam.open_attempt_id && exam.blocked_reason && (
        <p className="st-hint">{exam.blocked_reason}</p>
      )}
      <div className="st-card-actions">
        {action}
        {finished && (exam.can_start || exam.open_attempt_id) && (
          <Link className="st-link" to={`/student/result/${exam.last_attempt_id}`}>View last result</Link>
        )}
      </div>
    </article>
  );
}

export default function StudentDashboard() {
  const { user } = useAuth();
  const [exams, setExams] = useState(null);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [examRows, resultRows] = await Promise.all([fetchMyExams(), fetchMyResults()]);
      setExams(examRows);
      setResults(resultRows);
      setError("");
    } catch (err) {
      setError(err.message || "Could not load your exams.");
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 30000); // exams open and close while the page is open
    return () => clearInterval(id);
  }, [load]);

  const inProgress = (exams || []).filter((e) => e.open_attempt_id);

  return (
    <div className="st-page">
      <div className="st-page-header">
        <div>
          <h2>Welcome{user?.full_name ? `, ${user.full_name}` : ""}</h2>
          <p>Your assigned exams and results.</p>
        </div>
        <button type="button" className="st-btn ghost" onClick={load}>Refresh</button>
      </div>

      {error && <div className="st-alert danger">{error}</div>}

      {inProgress.length > 0 && (
        <div className="st-alert warn">
          You have an exam in progress: <strong>{inProgress[0].name}</strong>. Your timer is still running.{" "}
          <Link className="st-link" to={`/student/attempt/${inProgress[0].open_attempt_id}`}>Resume now</Link>
        </div>
      )}

      <section>
        <h3 className="st-section-title">My exams</h3>
        {exams === null && !error && <p className="st-muted">Loading your exams...</p>}
        {exams && exams.length === 0 && (
          <div className="st-empty">
            <strong>No exams yet</strong>
            <p>When an examiner assigns you to an exam it will appear here.</p>
          </div>
        )}
        <div className="st-grid">
          {(exams || []).map((exam) => <ExamCard key={exam.id} exam={exam} />)}
        </div>
      </section>

      <section>
        <h3 className="st-section-title">My results</h3>
        {results.length === 0 ? (
          <p className="st-muted">Your results will appear here after you submit an exam.</p>
        ) : (
          <div className="st-table-wrap">
            <table className="st-table">
              <thead>
                <tr><th>Exam</th><th>Attempt</th><th>Submitted</th><th>Score</th><th>Result</th><th /></tr>
              </thead>
              <tbody>
                {results.map((r) => (
                  <tr key={r.attempt_id}>
                    <td>{r.exam_name}</td>
                    <td>#{r.attempt_number}</td>
                    <td>{formatDateTime(r.submitted_at)}</td>
                    <td>{r.obtained_marks} / {r.total_marks} ({percentLabel(r.percentage)})</td>
                    <td>
                      {r.passed === null ? <span className="st-chip muted">Recorded</span>
                        : r.passed ? <span className="st-chip ok">Passed</span>
                        : <span className="st-chip danger">Not passed</span>}
                    </td>
                    <td><Link className="st-link" to={`/student/result/${r.attempt_id}`}>View</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
