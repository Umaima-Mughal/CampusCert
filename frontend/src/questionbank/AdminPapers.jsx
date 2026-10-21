import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchExams } from "../api/exams";
import { getPaper, listPapers } from "../api/questionsApi";
import McqBlock from "./McqBlock";

/**
 * Read-only list of the exam papers examiners have made (Member 3, shown inside Member 2's admin area).
 * Admins can look at a paper and see which exams use it. They cannot create or change papers;
 * a paper is assigned to an exam from that exam's own page.
 */
export default function AdminPapers() {
  const [papers, setPapers] = useState([]);
  const [usedBy, setUsedBy] = useState({});     // paper_id -> [exam, ...]
  const [open, setOpen] = useState(null);       // the paper being read
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([listPapers(), fetchExams()])
      .then(([list, exams]) => {
        if (cancelled) return;
        const map = {};
        exams.forEach((e) => {
          if (e.paper_id) (map[e.paper_id] ||= []).push(e);
        });
        setPapers(list);
        setUsedBy(map);
      })
      .catch((e) => { if (!cancelled) setError(e.message || "Could not load papers."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  async function view(id) {
    setError("");
    try {
      setOpen(await getPaper(id));
    } catch (e) {
      setError(e.message);
    }
  }

  if (open) {
    return (
      <div>
        <div className="admin-page-header">
          <div>
            <h3>{open.title}</h3>
            <p>
              {open.question_count} question{open.question_count === 1 ? "" : "s"} · {open.total_marks} mark
              {open.total_marks === 1 ? "" : "s"}
              {open.duration_minutes ? ` · ${open.duration_minutes} minutes` : ""}
            </p>
          </div>
          <div className="admin-actions">
            <button type="button" className="admin-btn" onClick={() => setOpen(null)}>Back to papers</button>
          </div>
        </div>
        <div className="admin-card">
          {open.instructions && <p className="admin-muted"><strong>Instructions:</strong> {open.instructions}</p>}
          <ol style={{ marginTop: 12, paddingLeft: 20 }}>
            {open.items.map((i) => (
              <li key={i.question.id} style={{ marginBottom: 12 }}>
                <p>{i.question.question}</p>
                <McqBlock q={i.question} />
                <span className="admin-muted">
                  [{i.marks} mark{i.marks === 1 ? "" : "s"}] · {i.question.difficulty} · {i.question.subject} / {i.question.topic}
                </span>
              </li>
            ))}
          </ol>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="admin-page-header">
        <div>
          <h3>Exam papers</h3>
          <p>Papers your examiners have made. Open an exam to assign one to it.</p>
        </div>
      </div>

      {error && <div className="admin-alert error">{error}</div>}
      {loading ? (
        <p className="admin-muted">Loading papers...</p>
      ) : papers.length === 0 ? (
        <div className="admin-card">
          <p className="admin-empty">No papers yet. An examiner has to create one first.</p>
        </div>
      ) : (
        <div className="admin-card">
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr><th>Title</th><th>Questions</th><th>Marks</th><th>Time</th><th>Used by</th><th></th></tr>
              </thead>
              <tbody>
                {papers.map((p) => (
                  <tr key={p.id}>
                    <td>{p.title}</td>
                    <td>{p.question_count}</td>
                    <td>{p.total_marks}</td>
                    <td>{p.duration_minutes ? `${p.duration_minutes} min` : "-"}</td>
                    <td>
                      {(usedBy[p.id] || []).length === 0
                        ? <span className="admin-muted">Not assigned</span>
                        : usedBy[p.id].map((e, n) => (
                            <span key={e.id}>
                              {n > 0 && ", "}
                              <Link className="admin-link" to={`/admin/exams/${e.id}`}>{e.name}</Link>
                            </span>
                          ))}
                    </td>
                    <td><button type="button" className="admin-link" onClick={() => view(p.id)}>View</button></td>
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
