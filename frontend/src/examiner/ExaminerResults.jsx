import { useCallback, useEffect, useState } from "react";
import { Navigate, Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { fetchExams } from "../api/exams";
import { getExamStudentResults } from "../api/examinerResults";

import "./results.css";

const STAFF = ["examiner", "admin", "super_admin"];

export default function ExaminerResults() {
  const { user, loading } = useAuth();

  if (loading) return <p>Loading student marks...</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (!STAFF.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <StudentMarks />;
}

function StudentMarks() {
  const [exams, setExams] = useState([]);
  const [examId, setExamId] = useState("");
  const [marks, setMarks] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    fetchExams()
      .then((data) => {
        if (cancelled) return;
        const rows = Array.isArray(data) ? data : data?.items || [];

        setExams(rows);
        if (rows.length) setExamId(String(rows[0].id));
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });

    return () => { cancelled = true; };
  }, []);

  const load = useCallback(async () => {
    if (!examId) return;

    try {
      const data = await getExamStudentResults(examId);
      setMarks(data.items || []);
      setError("");
    } catch (e) {
      setError(e.message || "Could not load student marks.");
    }
  }, [examId]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="res-page">
      <div className="res-shell">
        <header className="res-header">
          <div>
            <div className="res-eyebrow">
              CAMPUSCERT / EXAMINER
            </div>
            <h1>Student Marks</h1>
            <p>Marks obtained by each student in an exam.</p>
          </div>
          <Link className="res-link" to="/question-bank">
            Back to examiner portal
          </Link>
        </header>

        <section className="res-toolbar">
          <label htmlFor="res-exam">Select Exam</label>
          <select
            id="res-exam"
            value={examId}
            onChange={(e) => {
              setExamId(e.target.value);
              setMarks([]);
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

          <button type="button" onClick={load} disabled={!examId}>
            Refresh
          </button>
        </section>

        {error && (
          <div className="res-error" role="alert">
            {error}
          </div>
        )}

        <section className="res-panel">
          <div className="res-panel-head">
            <div>
              <h2>Results</h2>
              <p>Students who have not finished show "—".</p>
            </div>
            <span className="res-pill">
              {marks.length} attempts
            </span>
          </div>

          <div className="res-table-wrap">
            <table className="res-table">
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Attempt</th>
                  <th>Status</th>
                  <th>Marks</th>
                  <th>Percentage</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {marks.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="res-empty">
                      No student attempts for this exam.
                    </td>
                  </tr>
                ) : (
                  marks.map((row) => (
                    <tr key={row.attempt_id}>
                      <td>
                        <strong>{row.candidate_name}</strong>
                        <small>{row.candidate_email}</small>
                      </td>
                      <td>#{row.attempt_number}</td>
                      <td>{row.status}</td>
                      <td>
                        {row.obtained_marks == null
                          ? "—"
                          : `${row.obtained_marks} / ${row.total_marks}`}
                      </td>
                      <td>
                        {row.percentage == null
                          ? "—"
                          : `${Number(row.percentage).toFixed(1)}%`}
                      </td>
                      <td>
                        {row.passed == null
                          ? "—"
                          : row.passed ? "Pass" : "Fail"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
