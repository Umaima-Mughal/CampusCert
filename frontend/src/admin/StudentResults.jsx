import { useEffect, useMemo, useState } from "react";
import { fetchExams } from "../api/exams";
import { getExamStudentResults } from "../api/examinerResults";
import { buildResultsCsv, downloadCsv } from "./resultsCsv";

const ALL_PAPERS = "ALL";

/** "obtained / total", or just "obtained" if total is missing, or null if not graded. */
function formatScore(obtained, total) {
  if (obtained === null || obtained === undefined) return null;
  if (total === null || total === undefined) return String(obtained);
  return `${obtained} out of ${total}`;
}
/** CSV-only format. Excel "10 / 2" ko date bana deta hai, is liye "out of" use hota hai. */
function formatScoreForCsv(obtained, total) {
  if (obtained === null || obtained === undefined) return "";
  if (total === null || total === undefined) return String(obtained);
  return `${obtained} out of ${total}`;
}

function toSlug(text) {
  return String(text || "")
    .replace(/[^a-z0-9]+/gi, "_")
    .replace(/^_+|_+$/g, "") || "Paper";
}

export default function StudentResults() {
  const [exams, setExams] = useState([]);
  const [rows, setRows] = useState([]);
  const [selectedExamId, setSelectedExamId] = useState(ALL_PAPERS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");
      setWarning("");
      try {
        const data = await fetchExams();
        const examList = Array.isArray(data) ? data : data?.items || [];

        // Each exam's results come from the existing per-exam endpoint.
        // A failed exam is reported as a warning, never filled with placeholders.
        const perExam = await Promise.all(
          examList.map((exam) =>
            getExamStudentResults(exam.id)
              .then((res) => ({ exam, items: res?.items || [], failed: false }))
              .catch(() => ({ exam, items: [], failed: true }))
          )
        );

        if (cancelled) return;

        const built = [];
        let failedCount = 0;
        for (const { exam, items, failed } of perExam) {
          if (failed) {
            failedCount += 1;
            continue;
          }
          for (const item of items) {
            built.push({
              key: `${exam.id}-${item.attempt_id}`,
              examId: String(exam.id),
              paperName: exam.name ?? "",
              studentName: item.candidate_name ?? "",
              studentEmail: item.candidate_email ?? "",
              obtained: item.obtained_marks,
              total: item.total_marks,
            });
          }
        }

        setExams(examList);
        setRows(built);
        if (failedCount > 0) {
          setWarning(
            `Results could not be loaded for ${failedCount} paper${failedCount === 1 ? "" : "s"}. The rest are shown below.`
          );
        }
      } catch (err) {
        if (!cancelled) setError(err.message || "Could not load student results.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredRows = useMemo(
    () =>
      selectedExamId === ALL_PAPERS
        ? rows
        : rows.filter((row) => row.examId === selectedExamId),
    [rows, selectedExamId]
  );

  const selectedExam = exams.find((exam) => String(exam.id) === selectedExamId);

  // If the selected paper disappears after a reload, fall back to All Papers.
  useEffect(() => {
    if (
      selectedExamId !== ALL_PAPERS &&
      !exams.some((exam) => String(exam.id) === selectedExamId)
    ) {
      setSelectedExamId(ALL_PAPERS);
    }
  }, [exams, selectedExamId]);

  function handleDownload() {
    try {
      const csvRows = filteredRows.map((row) => ({
        studentName: row.studentName,
        studentEmail: row.studentEmail,
        paperName: row.paperName,
        resultText: formatScoreForCsv(row.obtained, row.total),
      }));
      const filename =
        selectedExamId === ALL_PAPERS
          ? "CampusCert_Student_Results.csv"
          : `CampusCert_${toSlug(selectedExam?.name)}_Results.csv`;
      downloadCsv(filename, buildResultsCsv(csvRows));
    } catch {
      setError("Could not generate the CSV file. Please try again.");
    }
  }

  return (
    <div>
      <div className="admin-page-header">
        <div>
          <h3>Student results</h3>
          <p>Examination results for students in your organization.</p>
        </div>
        <div className="admin-actions">
          <button
            type="button"
            className="admin-btn"
            onClick={handleDownload}
            disabled={loading || filteredRows.length === 0}
          >
            Download CSV
          </button>
        </div>
      </div>

      {error && <div className="admin-alert error">{error}</div>}
      {warning && <div className="admin-alert error">{warning}</div>}

      <div className="admin-card">
        <div className="admin-field">
          <label htmlFor="student-results-paper">Paper</label>
          <select
            id="student-results-paper"
            className="admin-filter"
            value={selectedExamId}
            onChange={(e) => setSelectedExamId(e.target.value)}
            disabled={loading}
          >
            <option value={ALL_PAPERS}>All Papers</option>
            {exams.map((exam) => (
              <option key={exam.id} value={String(exam.id)}>
                {exam.name}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <p className="admin-muted">Loading student results...</p>
        ) : filteredRows.length === 0 ? (
          <p className="admin-empty">
            {exams.length === 0
              ? "No exams found for your organization yet."
              : "No results available for this selection."}
          </p>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Student Name</th>
                  <th>Student Email</th>
                  <th>Paper / Examination</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((row) => (
                  <tr key={row.key}>
                    <td>{row.studentName || "—"}</td>
                    <td>{row.studentEmail || "—"}</td>
                    <td>{row.paperName || "—"}</td>
                    <td>{formatScore(row.obtained, row.total) ?? "—"}</td>
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