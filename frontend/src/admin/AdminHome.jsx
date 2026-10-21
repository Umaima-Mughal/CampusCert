import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchExamSummary, fetchExams } from "../api/exams";
import { apiErrorMessage, formatDateTime, statusLabel } from "./examUtils";

export default function AdminHome() {
  const [summary, setSummary] = useState(null);
  const [upcoming, setUpcoming] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchExamSummary(), fetchExams("SCHEDULED")])
      .then(([stats, scheduled]) => {
        if (cancelled) return;
        setSummary(stats);
        setUpcoming((scheduled || []).slice(0, 5));
      })
      .catch((err) => {
        if (!cancelled) setError(apiErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <p className="admin-muted">Loading dashboard...</p>;

  const byStatus = summary?.by_status || {};

  return (
    <div>
      <div className="admin-page-header">
        <div>
          <h3>University dashboard</h3>
          <p>Create exams, configure schedules, and assign candidates for your organization.</p>
        </div>
        <Link to="/admin/exams/new" className="admin-btn">Create exam</Link>
      </div>

      {error && <div className="admin-alert error">{error}</div>}

      <div className="admin-grid">
        <div className="admin-card">
          <h4>Total exams</h4>
          <div className="stat">{summary?.total ?? 0}</div>
        </div>
        <div className="admin-card">
          <h4>Scheduled</h4>
          <div className="stat">{summary?.upcoming ?? byStatus.SCHEDULED ?? 0}</div>
        </div>
        <div className="admin-card">
          <h4>Active</h4>
          <div className="stat">{byStatus.ACTIVE ?? 0}</div>
        </div>
        <div className="admin-card">
          <h4>Drafts</h4>
          <div className="stat">{byStatus.DRAFT ?? 0}</div>
        </div>
      </div>

      <div className="admin-card" style={{ marginTop: 18 }}>
        <h4>Upcoming scheduled exams</h4>
        {upcoming.length === 0 ? (
          <p className="admin-empty" style={{ marginTop: 12 }}>
            No scheduled exams yet. Create an exam and set a start window.
          </p>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Starts</th>
                  <th>Duration</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {upcoming.map((exam) => (
                  <tr key={exam.id}>
                    <td>
                      <Link className="admin-link" to={`/admin/exams/${exam.id}`}>
                        {exam.name}
                      </Link>
                    </td>
                    <td>{formatDateTime(exam.starts_at)}</td>
                    <td>{exam.duration_minutes} min</td>
                    <td><span className={`admin-badge ${exam.status}`}>{statusLabel(exam.status)}</span></td>
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
