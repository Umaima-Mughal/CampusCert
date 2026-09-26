import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteExam, fetchExams } from "../api/exams";
import { EXAM_STATUSES, apiErrorMessage, formatDateTime, statusLabel } from "./examUtils";

export default function ExamList() {
  const [exams, setExams] = useState([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");

  function load(nextStatus = status) {
    setLoading(true);
    setError("");
    fetchExams(nextStatus || undefined)
      .then(setExams)
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleDelete(exam) {
    if (!window.confirm(`Delete draft exam “${exam.name}”? This cannot be undone.`)) return;
    setBusyId(exam.id);
    setError("");
    try {
      await deleteExam(exam.id);
      setExams((current) => current.filter((item) => item.id !== exam.id));
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setBusyId("");
    }
  }

  return (
    <div>
      <div className="admin-page-header">
        <div>
          <h3>Exams</h3>
          <p>All exams for your organization, including drafts, schedules, and closed sittings.</p>
        </div>
        <div className="admin-actions">
          <select
            className="admin-filter"
            value={status}
            onChange={(e) => {
              const value = e.target.value;
              setStatus(value);
              load(value);
            }}
            style={{
              padding: "10px 12px",
              borderRadius: 11,
              border: "1px solid rgba(255,255,255,0.09)",
              background: "rgba(255,255,255,0.045)",
              color: "#fff",
            }}
          >
            <option value="">All statuses</option>
            {EXAM_STATUSES.map((item) => (
              <option key={item} value={item}>{statusLabel(item)}</option>
            ))}
          </select>
          <Link to="/admin/exams/new" className="admin-btn">Create exam</Link>
        </div>
      </div>

      {error && <div className="admin-alert error">{error}</div>}
      {loading ? (
        <p className="admin-muted">Loading exams...</p>
      ) : exams.length === 0 ? (
        <div className="admin-card">
          <p className="admin-empty">No exams match this filter. Create one to get started.</p>
        </div>
      ) : (
        <div className="admin-card">
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Duration</th>
                  <th>Window</th>
                  <th>Candidates</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {exams.map((exam) => (
                  <tr key={exam.id}>
                    <td>
                      <Link className="admin-link" to={`/admin/exams/${exam.id}`}>
                        {exam.name}
                      </Link>
                    </td>
                    <td><span className={`admin-badge ${exam.status}`}>{statusLabel(exam.status)}</span></td>
                    <td>{exam.duration_minutes} min</td>
                    <td>
                      {exam.starts_at ? `${formatDateTime(exam.starts_at)} – ${formatDateTime(exam.ends_at)}` : "Not scheduled"}
                    </td>
                    <td>{exam.candidate_count}</td>
                    <td>
                      <div className="admin-actions">
                        <Link className="admin-btn secondary small" to={`/admin/exams/${exam.id}`}>View</Link>
                        {(exam.status === "DRAFT" || exam.status === "SCHEDULED") && (
                          <Link className="admin-btn secondary small" to={`/admin/exams/${exam.id}/edit`}>Edit</Link>
                        )}
                        {exam.status === "DRAFT" && (
                          <button
                            type="button"
                            className="admin-btn danger small"
                            disabled={busyId === exam.id}
                            onClick={() => handleDelete(exam)}
                          >
                            Delete
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
