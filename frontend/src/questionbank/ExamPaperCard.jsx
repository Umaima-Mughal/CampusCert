import { useEffect, useState } from "react";
import { getPaper } from "../api/questionsApi";
import PaperPicker from "./PaperPicker";

/**
 * Question paper of an exam, shown on the admin's exam page.
 * Papers are built by examiners; the admin chooses which one this exam uses.
 *   canAssign: false once the exam is live / closed (the API refuses changes then),
 *              except a live exam whose paper is empty, which may still be fixed
 *   status: the exam's status, used to explain why the paper is locked
 *   onAssign(paperId | null): saves the choice (ExamDetail handles the request)
 */
export default function ExamPaperCard({ paperId, examDuration, canAssign, status, busy, onAssign }) {
  const [paper, setPaper] = useState(null);
  const [error, setError] = useState("");
  const [choice, setChoice] = useState("");

  useEffect(() => {
    setPaper(null);
    setError("");
    setChoice("");
    if (!paperId) return undefined;
    let cancelled = false;
    getPaper(paperId)
      .then((p) => { if (!cancelled) setPaper(p); })
      .catch((e) => { if (!cancelled) setError(e.message); });
    return () => { cancelled = true; };
  }, [paperId]);

  return (
    <div style={{ marginTop: 16 }}>
      <h4>Question paper</h4>

      {!paperId && (
        <p className="admin-empty" style={{ marginTop: 8 }}>
          No paper assigned yet. The exam can't be activated until one is.
        </p>
      )}
      {paperId && error && <p className="admin-muted" style={{ marginTop: 8 }}>{error}</p>}
      {paperId && !error && !paper && <p className="admin-muted" style={{ marginTop: 8 }}>Loading paper...</p>}
      {paper && (
        <>
          <p className="admin-muted" style={{ marginTop: 8 }}>
            <strong>{paper.title}</strong> · {paper.question_count} question{paper.question_count === 1 ? "" : "s"} ·{" "}
            {paper.total_marks} mark{paper.total_marks === 1 ? "" : "s"}
          </p>
          {paper.question_count === 0 && (
            <div className="admin-alert error" style={{ marginTop: 8 }}>
              This paper has no questions, so students would see an empty exam.
              {canAssign
                ? " Choose another paper below, or remove this one."
                : " Deactivate the exam, then choose another paper or remove this one."}
            </div>
          )}
          {paper.duration_minutes && examDuration && paper.duration_minutes !== examDuration && (
            <p className="admin-help" style={{ marginTop: 6 }}>
              Note: the paper suggests {paper.duration_minutes} minutes, but this exam is set to {examDuration}.
              The exam's duration is the one that applies.
            </p>
          )}
        </>
      )}

      {canAssign ? (
        <div style={{ marginTop: 10 }}>
          <PaperPicker value={choice} onChange={(id) => setChoice(id)} />
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <button
              type="button"
              className="admin-btn"
              disabled={!choice || busy}
              onClick={() => onAssign(Number(choice))}
            >
              {busy ? "Saving..." : paperId ? "Change paper" : "Assign paper"}
            </button>
            {paperId && (
              <button type="button" className="admin-btn" disabled={busy} onClick={() => onAssign(null)}>
                Remove paper
              </button>
            )}
          </div>
          {status === "ACTIVE" && paperId && (
            <p className="admin-help" style={{ marginTop: 6 }}>
              Removing the paper takes this exam out of the live window until you attach another one.
            </p>
          )}
        </div>
      ) : (
        <p className="admin-help" style={{ marginTop: 8 }}>
          {status === "ACTIVE"
            ? "This exam is live. Deactivate it to change or remove its paper."
            : "The paper can't be changed once the exam is closed."}
        </p>
      )}
    </div>
  );
}
