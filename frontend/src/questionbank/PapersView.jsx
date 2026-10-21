import { useCallback, useEffect, useState } from "react";
import { deletePaper, getPaper, listPapers } from "../api/questionsApi";
import McqBlock from "./McqBlock";
import PaperEditor from "./PaperEditor";

function paperCsv(p) {
  const esc = (v) => `"${String(v).replace(/"/g, '""')}"`;
  const rows = [["No", "Subject", "Difficulty", "Topic", "Question", "Option A", "Option B", "Option C", "Option D", "Correct Answer", "Solution", "Marks"],
    ...p.items.map((i) => [i.position, i.question.subject, i.question.difficulty, i.question.topic, i.question.question,
      i.question.option_a ?? "", i.question.option_b ?? "", i.question.option_c ?? "", i.question.option_d ?? "",
      i.question.correct_option ?? "", i.question.solution ?? "", i.marks])];
  return rows.map((r) => r.map(esc).join(",")).join("\r\n");
}

export default function PapersView({ focusId }) {
  const [papers, setPapers] = useState([]);
  const [current, setCurrent] = useState(null);   // the paper being viewed
  const [editing, setEditing] = useState(false);
  const [showAnswers, setShowAnswers] = useState(false);   // off by default so a printed paper is safe to hand out
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true); setError("");
    try { setPapers(await listPapers()); } catch (e) { setError(e.message); } finally { setLoading(false); }
  }, []);

  const open = useCallback(async (id) => {
    setError("");
    try { setCurrent(await getPaper(id)); setEditing(false); } catch (e) { setError(e.message); }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => { if (focusId) open(focusId); }, [focusId, open]);

  async function remove(p) {
    if (!window.confirm(`Delete the paper "${p.title}"? The questions stay in your question bank.`)) return;
    try { await deletePaper(p.id); setCurrent(null); await refresh(); } catch (e) { setError(e.message); }
  }

  function download() {
    const blob = new Blob(["\ufeff" + paperCsv(current)], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${current.title.replace(/[^\w-]+/g, "_")}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  if (current && editing) {
    return (
      <PaperEditor paper={current}
        initialItems={current.items.map((i) => ({ question: i.question, marks: i.marks }))}
        onCancel={() => setEditing(false)}
        onSaved={(p) => { setCurrent(p); setEditing(false); refresh(); }} />
    );
  }

  if (current) {
    return (
      <>
        <div className="qb-toolbar qb-noprint">
          <button className="qb-btn" onClick={() => { setCurrent(null); refresh(); }}>Back to all papers</button>
          <button className="qb-btn" onClick={() => setEditing(true)}>Edit</button>
          <button className="qb-btn" onClick={() => window.print()}>Print</button>
          <button className="qb-btn" onClick={download}>Download CSV</button>
          <label style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <input type="checkbox" checked={showAnswers} onChange={(e) => setShowAnswers(e.target.checked)} />
            Show answers &amp; solutions
          </label>
          <button className="qb-link qb-link--danger" onClick={() => remove(current)}>Delete paper</button>
        </div>
        {error && <p className="qb-error" role="alert">{error}</p>}
        <article className="qb-paper">
          <h2>{current.title}</h2>
          <p className="qb-paper-meta">
            {current.question_count} question{current.question_count === 1 ? "" : "s"} · {current.total_marks} mark{current.total_marks === 1 ? "" : "s"}
            {current.duration_minutes ? ` · ${current.duration_minutes} minutes` : ""}
          </p>
          {current.instructions && <p className="qb-paper-instr"><strong>Instructions:</strong> {current.instructions}</p>}
          <ol>
            {current.items.map((i) => (
              <li key={i.question.id}>
                <p>{i.question.question}</p>
                <McqBlock q={i.question} showAnswer={showAnswers} />
                <span className="qb-paper-tag">
                  [{i.marks} mark{i.marks === 1 ? "" : "s"}] <span className="qb-noprint">· {i.question.difficulty} · {i.question.subject} / {i.question.topic}</span>
                </span>
              </li>
            ))}
          </ol>
        </article>
      </>
    );
  }

  return (
    <>
      {error && <p className="qb-error" role="alert">{error}</p>}
      <div className="qb-table-wrap">
        <table>
          <thead>
            <tr><th>Title</th><th>Questions</th><th>Marks</th><th>Time</th><th>Created</th><th><span className="sr">Actions</span></th></tr>
          </thead>
          <tbody>
            {papers.map((p) => (
              <tr key={p.id}>
                <td>{p.title}</td>
                <td>{p.question_count}</td>
                <td>{p.total_marks}</td>
                <td>{p.duration_minutes ? `${p.duration_minutes} min` : "-"}</td>
                <td>{p.created_at ? new Date(p.created_at).toLocaleDateString() : ""}</td>
                <td>
                  <button className="qb-link" onClick={() => open(p.id)}>Open</button>{" "}
                  <button className="qb-link qb-link--danger" onClick={() => remove(p)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {loading && <div className="qb-empty">Loading papers…</div>}
        {!loading && papers.length === 0 && (
          <div className="qb-empty">
            No exam papers yet. Tick questions in the Question bank tab, or use Generate paper.
          </div>
        )}
      </div>
    </>
  );
}
