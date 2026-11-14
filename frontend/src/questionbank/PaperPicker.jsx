import { useEffect, useRef, useState } from "react";
import { listPapers } from "../api/questionsApi";

/**
 * Dropdown of the organization's exam papers (Member 3), used by the exam form (Member 2).
 *   value:           paper id as a string ("" = none)
 *   onChange(id, p): id is a string, p the paper summary (or undefined when cleared)
 *   onInitialPaper:  called once when a preselected paper (e.g. ?paper=12) has loaded
 */
export default function PaperPicker({ id, value, onChange, onInitialPaper }) {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const announced = useRef(false);

  useEffect(() => {
    let cancelled = false;
    listPapers()
      .then((list) => { if (!cancelled) setPapers(list); })
      .catch((e) => { if (!cancelled) setError(e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (announced.current || !value || papers.length === 0) return;
    const paper = papers.find((p) => String(p.id) === String(value));
    if (paper) {
      announced.current = true;
      onInitialPaper?.(paper);
    }
  }, [papers, value, onInitialPaper]);

  const known = papers.some((p) => String(p.id) === String(value));

  return (
    <>
      <select
        id={id}
        value={value}
        disabled={loading}
        onChange={(e) => onChange(e.target.value, papers.find((p) => String(p.id) === e.target.value))}
      >
        <option value="">{loading ? "Loading papers..." : "No paper yet (attach later)"}</option>
        {value && !known && !loading && <option value={value}>Paper #{value} (not found)</option>}
        {papers.map((p) => (
          <option key={p.id} value={p.id}>
            {p.title} — {p.question_count} question{p.question_count === 1 ? "" : "s"}, {p.total_marks} marks
          </option>
        ))}
      </select>
      {error && <p className="admin-help" role="alert">{error}</p>}
      {!loading && !error && papers.length === 0 && (
        <p className="admin-help">
          No papers yet. An examiner needs to create one in the question bank first.
        </p>
      )}
    </>
  );
}
