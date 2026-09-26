import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  activateExam,
  archiveExam,
  assignExamCandidates,
  closeExam,
  deactivateExam,
  deleteExam,
  fetchEligibleCandidates,
  fetchExam,
  fetchExamCandidates,
  removeExamCandidate,
  scheduleExam,
} from "../api/exams";
import {
  apiErrorMessage,
  formatDateTime,
  statusLabel,
  toDateTimeLocal,
  toIsoOrNull,
} from "./examUtils";

export default function ExamDetail() {
  const { examId } = useParams();
  const navigate = useNavigate();
  const [exam, setExam] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [eligible, setEligible] = useState([]);
  const [selected, setSelected] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");

  async function reload() {
    const [examData, assigned, pool] = await Promise.all([
      fetchExam(examId),
      fetchExamCandidates(examId),
      fetchEligibleCandidates(),
    ]);
    setExam(examData);
    setCandidates(assigned || []);
    setEligible(pool || []);
    setStartsAt(toDateTimeLocal(examData.starts_at));
    setEndsAt(toDateTimeLocal(examData.ends_at));
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    reload()
      .catch((err) => {
        if (!cancelled) setError(apiErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [examId]);

  async function runAction(key, action, okMessage) {
    setBusy(key);
    setError("");
    setSuccess("");
    try {
      await action();
      await reload();
      if (okMessage) setSuccess(okMessage);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setBusy("");
    }
  }

  async function handleSchedule(e) {
    e.preventDefault();
    const starts = toIsoOrNull(startsAt);
    const ends = toIsoOrNull(endsAt);
    if (!starts || !ends) {
      setError("Both start and end times are required to schedule an exam.");
      return;
    }
    await runAction("schedule", () => scheduleExam(examId, { starts_at: starts, ends_at: ends }), "Schedule saved.");
  }

  async function handleAssign(e) {
    e.preventDefault();
    if (!selected) {
      setError("Select a student to assign.");
      return;
    }
    await runAction("assign", () => assignExamCandidates(examId, [selected]), "Candidate assigned.");
    setSelected("");
  }

  async function handleDelete() {
    if (!window.confirm(`Delete draft exam “${exam.name}”?`)) return;
    setBusy("delete");
    setError("");
    try {
      await deleteExam(examId);
      navigate("/admin/exams");
    } catch (err) {
      setError(apiErrorMessage(err));
      setBusy("");
    }
  }

  if (loading) return <p className="admin-muted">Loading exam...</p>;
  if (!exam) return <div className="admin-alert error">{error || "Exam not found."}</div>;

  const assignedIds = new Set(candidates.map((item) => item.id));
  const available = eligible.filter((item) => !assignedIds.has(item.id));
  const canConfigure = exam.status === "DRAFT" || exam.status === "SCHEDULED";
  const distribution = Object.entries(exam.distribution || {});

  return (
    <div>
      <div className="admin-page-header">
        <div>
          <h3>{exam.name}</h3>
          <p>Configure this sitting, manage its lifecycle, and assign candidates.</p>
        </div>
        <div className="admin-actions">
          <Link to="/admin/exams" className="admin-btn secondary">All exams</Link>
          {canConfigure && (
            <Link to={`/admin/exams/${exam.id}/edit`} className="admin-btn">Edit configuration</Link>
          )}
        </div>
      </div>

      {error && <div className="admin-alert error">{error}</div>}
      {success && <div className="admin-alert success">{success}</div>}

      <div className="admin-detail-grid">
        <div className="admin-card">
          <h4>Configuration</h4>
          <dl className="admin-dl" style={{ marginTop: 14 }}>
            <dt>Status</dt>
            <dd><span className={`admin-badge ${exam.status}`}>{statusLabel(exam.status)}</span></dd>
            <dt>Duration</dt>
            <dd>{exam.duration_minutes} minutes</dd>
            <dt>Window</dt>
            <dd>
              {exam.starts_at
                ? `${formatDateTime(exam.starts_at)} – ${formatDateTime(exam.ends_at)}`
                : "Not scheduled"}
            </dd>
            <dt>Passing score</dt>
            <dd>{exam.passing_score == null ? "Not set" : `${exam.passing_score}%`}</dd>
            <dt>Max attempts</dt>
            <dd>{exam.max_attempts}</dd>
            <dt>Shuffle questions</dt>
            <dd>{exam.shuffle_questions ? "Yes" : "No"}</dd>
            <dt>Late join</dt>
            <dd>{exam.late_join_minutes} minutes</dd>
            <dt>Candidates</dt>
            <dd>{exam.candidate_count}</dd>
          </dl>
          {exam.description && (
            <p className="admin-muted" style={{ marginTop: 16 }}>{exam.description}</p>
          )}
          {exam.instructions && (
            <p className="admin-muted" style={{ marginTop: 12 }}><strong>Instructions:</strong> {exam.instructions}</p>
          )}
          <div style={{ marginTop: 16 }}>
            <h4>Question distribution</h4>
            {distribution.length === 0 ? (
              <p className="admin-empty" style={{ marginTop: 8 }}>
                None set. Member 3 can still attach a question bank later.
              </p>
            ) : (
              <ul className="admin-muted" style={{ marginTop: 8, paddingLeft: 18 }}>
                {distribution.map(([subjectId, count]) => (
                  <li key={subjectId}>{subjectId}: {count} question(s)</li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="admin-card">
          <h4>Lifecycle</h4>
          <p className="admin-help" style={{ margin: "10px 0 14px" }}>
            Active exams are the ones Member 4 can start attempts against.
            Closing an exam ends that window.
          </p>
          <div className="admin-actions">
            {(exam.status === "DRAFT" || exam.status === "SCHEDULED") && (
              <button
                type="button"
                className="admin-btn"
                disabled={Boolean(busy)}
                onClick={() => runAction("activate", () => activateExam(exam.id), "Exam is now active.")}
              >
                {busy === "activate" ? "Activating..." : "Activate"}
              </button>
            )}
            {(exam.status === "ACTIVE" || exam.status === "SCHEDULED") && (
              <button
                type="button"
                className="admin-btn secondary"
                disabled={Boolean(busy)}
                onClick={() => runAction("deactivate", () => deactivateExam(exam.id), "Exam deactivated.")}
              >
                {busy === "deactivate" ? "Saving..." : "Deactivate"}
              </button>
            )}
            {(exam.status === "ACTIVE" || exam.status === "SCHEDULED") && (
              <button
                type="button"
                className="admin-btn secondary"
                disabled={Boolean(busy)}
                onClick={() => runAction("close", () => closeExam(exam.id), "Exam closed.")}
              >
                Close
              </button>
            )}
            {(exam.status === "DRAFT" || exam.status === "CLOSED") && (
              <button
                type="button"
                className="admin-btn secondary"
                disabled={Boolean(busy)}
                onClick={() => runAction("archive", () => archiveExam(exam.id), "Exam archived.")}
              >
                Archive
              </button>
            )}
            {exam.status === "DRAFT" && (
              <button
                type="button"
                className="admin-btn danger"
                disabled={Boolean(busy)}
                onClick={handleDelete}
              >
                Delete draft
              </button>
            )}
          </div>

          {canConfigure && (
            <form onSubmit={handleSchedule} style={{ marginTop: 20 }}>
              <h4>Schedule</h4>
              <div className="admin-field" style={{ marginTop: 10 }}>
                <label htmlFor="detail-start">Starts at</label>
                <input
                  id="detail-start"
                  type="datetime-local"
                  value={startsAt}
                  onChange={(e) => setStartsAt(e.target.value)}
                />
              </div>
              <div className="admin-field">
                <label htmlFor="detail-end">Ends at</label>
                <input
                  id="detail-end"
                  type="datetime-local"
                  value={endsAt}
                  onChange={(e) => setEndsAt(e.target.value)}
                />
              </div>
              <button type="submit" className="admin-btn" disabled={busy === "schedule"}>
                {busy === "schedule" ? "Saving..." : "Save schedule"}
              </button>
            </form>
          )}
        </div>
      </div>

      <div className="admin-card" style={{ marginTop: 16 }}>
        <h4>Candidates</h4>
        <p className="admin-help" style={{ margin: "8px 0 14px" }}>
          Only active students in this organization can be assigned. Attempts
          themselves are created by Member 4 when a student starts the exam.
        </p>
        {exam.status !== "ARCHIVED" && (
          <form className="admin-actions" onSubmit={handleAssign} style={{ marginBottom: 16 }}>
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              style={{
                minWidth: 260,
                padding: "10px 12px",
                borderRadius: 11,
                border: "1px solid rgba(255,255,255,0.09)",
                background: "rgba(255,255,255,0.045)",
                color: "#fff",
              }}
            >
              <option value="">Select a student</option>
              {available.map((student) => (
                <option key={student.id} value={student.id}>
                  {student.full_name} ({student.email})
                </option>
              ))}
            </select>
            <button type="submit" className="admin-btn" disabled={busy === "assign" || available.length === 0}>
              Assign
            </button>
          </form>
        )}
        {available.length === 0 && exam.status !== "ARCHIVED" && (
          <p className="admin-empty" style={{ marginBottom: 12 }}>
            No unassigned students found for this organization. Students must register
            with the same organization as this admin account.
          </p>
        )}
        {candidates.length === 0 ? (
          <p className="admin-empty">No candidates assigned yet.</p>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((student) => (
                  <tr key={student.id}>
                    <td>{student.full_name}</td>
                    <td>{student.email}</td>
                    <td>
                      {exam.status !== "ARCHIVED" && (
                        <button
                          type="button"
                          className="admin-btn danger small"
                          onClick={() =>
                            runAction(
                              `remove-${student.id}`,
                              () => removeExamCandidate(exam.id, student.id),
                              "Candidate removed."
                            )
                          }
                        >
                          Remove
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
