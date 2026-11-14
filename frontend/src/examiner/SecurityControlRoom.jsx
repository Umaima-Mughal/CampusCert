
import { useCallback, useEffect, useState } from "react";
import { Navigate, Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { fetchExams } from "../api/exams";
import {
  getExamSecurityOverview,
  getSecurityReviewQueue,
  getAttemptSecurityTimeline,
  resumeExamAttempt,
  terminateExamAttempt,
} from "../api/security";

import "./security.css";

const STAFF = ["examiner", "admin", "super_admin"];

function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

function Metric({ label, value }) {
  return (
    <div className="sec-metric">
      <span>{label}</span>
      <strong>{value ?? 0}</strong>
    </div>
  );
}

export default function SecurityControlRoom() {
  const { user, loading } = useAuth();

  if (loading) return <p>Loading security center...</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (!STAFF.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <SecurityCenter />;
}

function SecurityCenter() {
  const [exams, setExams] = useState([]);
  const [examId, setExamId] = useState("");
  const [overview, setOverview] = useState(null);
  const [queue, setQueue] = useState([]);
  const [timeline, setTimeline] = useState(null);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [updatedAt, setUpdatedAt] = useState(null);

  useEffect(() => {
    let cancelled = false;

    fetchExams()
      .then((data) => {
        if (cancelled) return;
        const rows = Array.isArray(data)
          ? data
          : data?.items || [];

        setExams(rows);
        if (rows.length) setExamId(String(rows[0].id));
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });

    return () => { cancelled = true; };
  }, []);

  const refresh = useCallback(async () => {
    if (!examId) return;

    try {
      const [stats, review] = await Promise.all([
        getExamSecurityOverview(examId),
        getSecurityReviewQueue(examId),
      ]);

      setOverview(stats);
      setQueue(review.items || []);
      setUpdatedAt(new Date());
      setError("");
    } catch (e) {
      setError(e.message || "Could not load security data.");
    }
  }, [examId]);

  useEffect(() => {
    if (!examId) return undefined;

    refresh();

    // Poll every five seconds; no WebSocket required.
    const interval = setInterval(refresh, 5000);

    return () => clearInterval(interval);
  }, [examId, refresh]);

  async function reviewAttempt(row) {
    setSelected(row);
    setTimeline(null);
    setError("");

    try {
      const result = await getAttemptSecurityTimeline(
        row.attempt_id
      );
      setTimeline(result);
    } catch (e) {
      setError(e.message);
    }
  }

  async function examinerAction(action) {
    if (!selected || busy) return;

    const description =
      action === "resume" ? "Resume" : "Terminate";

    if (!window.confirm(
      `${description} the exam for ${selected.candidate_name}?`
    )) return;

    const reason = window.prompt(
      "Enter a reason for the audit trail:"
    );

    if (!reason?.trim()) {
      setNotice("A review reason is required.");
      return;
    }

    setBusy(true);
    setError("");
    setNotice("");

    try {
      if (action === "resume") {
        await resumeExamAttempt(
          selected.attempt_id,
          reason.trim()
        );
      } else {
        await terminateExamAttempt(
          selected.attempt_id,
          reason.trim()
        );
      }

      setNotice(`Exam ${action} action completed.`);
      const attemptId = selected.attempt_id;

      await refresh();

      const next = await getAttemptSecurityTimeline(
        attemptId
      );
      setTimeline(next);
      setSelected(null);
    } catch (e) {
      setError(e.message || "Action failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="sec-page">
      <div className="sec-shell">
        <header className="sec-header">
          <div>
            <div className="sec-eyebrow">
              CAMPUSCERT / EXAM INTEGRITY
            </div>
            <h1>Security Control Room</h1>
            <p>
              Monitor exam incidents, review evidence and
              take authorized action.
            </p>
          </div>
          <Link className="sec-link" to="/">
            Back to portal
          </Link>
        </header>

        <section className="sec-toolbar">
          <label htmlFor="sec-exam">Select Exam</label>
          <select
            id="sec-exam"
            value={examId}
            onChange={(e) => {
              setExamId(e.target.value);
              setSelected(null);
              setTimeline(null);
              setOverview(null);
              setQueue([]);
            }}
          >
            {exams.length === 0 && (
              <option value="">No exams available</option>
            )}
            {exams.map((exam) => (
              <option key={exam.id} value={exam.id}>
                {exam.name}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={refresh}
            disabled={!examId || busy}
          >
            Refresh
          </button>

          <span className="sec-muted">
            Auto-refresh: 5 seconds
            {updatedAt &&
              ` · Last updated ${updatedAt.toLocaleTimeString()}`}
          </span>
        </section>

        {error && (
          <div className="sec-error" role="alert">
            {error}
          </div>
        )}
        {notice && (
          <div className="sec-notice" role="status">
            {notice}
          </div>
        )}

        <section className="sec-stats">
          <Metric
            label="Total Candidates"
            value={overview?.total_candidates}
          />
          <Metric
            label="Active"
            value={overview?.active}
          />
          <Metric
            label="Completed"
            value={overview?.completed}
          />
          <Metric
            label="Flagged"
            value={overview?.flagged}
          />
          <Metric
            label="Frozen"
            value={overview?.frozen}
          />
        </section>

        <section className="sec-panel">
          <div className="sec-panel-head">
            <div>
              <h2>Security Review Queue</h2>
              <p>
                Flagged candidates sorted by review priority.
              </p>
            </div>
            <span className="sec-pill">
              {queue.length} flagged
            </span>
          </div>

          <div className="sec-table-wrap">
            <table className="sec-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Status</th>
                  <th>Latest Event</th>
                  <th>Violations</th>
                  <th>Risk</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {queue.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="sec-empty">
                      No flagged attempts for this exam.
                    </td>
                  </tr>
                ) : (
                  queue.map((row) => (
                    <tr key={row.attempt_id}>
                      <td>
                        <strong>{row.candidate_name}</strong>
                        <small>{row.candidate_email}</small>
                      </td>
                      <td>{row.status}</td>
                      <td>
                        {row.latest_event}
                        <small>
                          {formatDate(row.latest_event_at)}
                        </small>
                      </td>
                      <td>{row.violation_count}</td>
                      <td>
                        <span className={
                          `sec-risk ${row.risk_level.toLowerCase()}`
                        }>
                          {row.risk_score} · {row.risk_level}
                        </span>
                      </td>
                      <td>
                        <button
                          type="button"
                          onClick={() => reviewAttempt(row)}
                        >
                          Review
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        {selected && (
          <section className="sec-panel">
            <div className="sec-panel-head">
              <div>
                <h2>Incident Investigation</h2>
                <p>{selected.candidate_name}</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setSelected(null);
                  setTimeline(null);
                }}
              >
                Close
              </button>
            </div>

            <p>
              Attempt: <code>{selected.attempt_id}</code>
            </p>
            <p>
              Status: <strong>{selected.status}</strong>
            </p>
            <p>
              Risk score: <strong>
                {selected.risk_score}
              </strong>
            </p>

            <h3>Audit Timeline</h3>

            {!timeline ? (
              <p>Loading audit history...</p>
            ) : (
              <ul className="sec-timeline">
                {(timeline.timeline || []).map((entry, i) => (
                  <li key={i}>
                    <strong>{entry.type}</strong>
                    <span>{formatDate(entry.at)}</span>
                    {entry.note && <p>{entry.note}</p>}
                  </li>
                ))}
              </ul>
            )}

            {selected.status === "FROZEN" && (
              <div className="sec-actions">
                <button
                  type="button"
                  disabled={busy}
                  className="sec-resume"
                  onClick={() => examinerAction("resume")}
                >
                  Resume Exam
                </button>
                <button
                  type="button"
                  disabled={busy}
                  className="sec-terminate"
                  onClick={() => examinerAction("terminate")}
                >
                  Terminate Exam
                </button>
              </div>
            )}
          </section>
        )}

        <footer className="sec-footer">
          Risk scores are review signals, not proof of cheating.
          Final decisions remain with authorized examiners.
        </footer>
      </div>
    </div>
  );
}
