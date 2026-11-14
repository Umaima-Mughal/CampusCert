import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { fetchAttempt, saveAnswer, submitAttempt } from "../api/attempts";
import { formatClock, isNetworkError, questionState, sleep, summarize, timerTone } from "./studentUtils";
import "./student.css";

const LETTERS = ["A", "B", "C", "D"];
const FINISHED = ["SUBMITTED", "TERMINATED"];
const SAVE_TEXT = {
  saved: "All answers saved",
  saving: "Saving...",
  offline: "No connection - retrying automatically",
  paused: "Saving paused",
};

/**
 * The exam screen.
 *  - The clock comes from the SERVER (remaining_seconds) and is re-synced every 20 s,
 *    so refreshing the page or changing the computer clock cannot add time.
 *  - Every click is saved straight away (autosave). Failed saves stay in a queue and are
 *    retried until they succeed, so a dropped connection does not lose answers.
 *  - When the time reaches zero the exam is submitted automatically.
 */
export default function ExamPage() {
  const { attemptId } = useParams();
  const navigate = useNavigate();

  const [exam, setExam] = useState(null); // { name, questions }
  const [loadError, setLoadError] = useState("");
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState({}); // question id -> "A".."D" | null
  const [marked, setMarked] = useState({}); // question id -> boolean
  const [status, setStatus] = useState("ACTIVE");
  const [remaining, setRemaining] = useState(null);
  const [saveState, setSaveState] = useState("saved");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState("");

  const endAtRef = useRef(0); // when the exam ends, in this computer's clock
  const queueRef = useRef(new Map()); // question id -> payload still waiting to be saved
  const flushingRef = useRef(false);
  const retryRef = useRef(null);
  const flushRef = useRef(() => {});
  const finishedRef = useRef(false);
  const submittingRef = useRef(false);
  const mountedRef = useRef(true);

  const goToResult = useCallback(() => {
    finishedRef.current = true;
    navigate(`/student/result/${attemptId}`, { replace: true });
  }, [attemptId, navigate]);

  /** Apply what the server says about the attempt. Returns false if the attempt is over. */
  const applyServerState = useCallback((view) => {
    if (FINISHED.includes(view.status)) {
      goToResult();
      return false;
    }
    setStatus(view.status);
    endAtRef.current = Date.now() + view.remaining_seconds * 1000;
    return true;
  }, [goToResult]);

  // ---------------------------------------------------------------- load
  useEffect(() => {
    mountedRef.current = true;
    let cancelled = false;
    fetchAttempt(attemptId)
      .then((view) => {
        if (cancelled || !applyServerState(view)) return;
        setExam({ name: view.exam_name, questions: view.questions });
        setAnswers(Object.fromEntries(view.questions.map((q) => [q.id, q.selected])));
        setMarked(Object.fromEntries(view.questions.map((q) => [q.id, q.marked_for_review])));
        setRemaining(view.remaining_seconds);
      })
      .catch((err) => !cancelled && setLoadError(err.message || "Could not load the exam."));
    return () => {
      cancelled = true;
      mountedRef.current = false;
      clearTimeout(retryRef.current);
    };
  }, [attemptId, applyServerState]);

  // ---------------------------------------------------------------- autosave
  const scheduleRetry = useCallback(() => {
    if (retryRef.current) return;
    retryRef.current = setTimeout(() => {
      retryRef.current = null;
      flushRef.current();
    }, 3000);
  }, []);

  /** The server refused an answer (not a network problem). Find out why. */
  const handleRejected = useCallback(async (err, questionId) => {
    try {
      const view = await fetchAttempt(attemptId);
      if (!applyServerState(view)) return "finished";
      if (view.status === "FROZEN") {
        setSaveState("paused");
        return "paused";
      }
    } catch (checkError) {
      if (isNetworkError(checkError)) return "offline";
    }
    setNotice(err.message || "An answer could not be saved.");
    queueRef.current.delete(questionId);
    return "dropped";
  }, [attemptId, applyServerState]);

  const flush = useCallback(async () => {
    if (flushingRef.current) return;
    flushingRef.current = true;
    try {
      if (queueRef.current.size === 0) return;
      setSaveState("saving");
      while (queueRef.current.size > 0) {
        const [questionId, payload] = queueRef.current.entries().next().value;
        try {
          await saveAnswer(attemptId, payload);
          // keep it queued if the student changed their mind while this was in flight
          if (queueRef.current.get(questionId) === payload) queueRef.current.delete(questionId);
        } catch (err) {
          if (isNetworkError(err)) {
            setSaveState("offline");
            scheduleRetry();
            return;
          }
          const outcome = await handleRejected(err, questionId);
          if (outcome === "finished") return;
          if (outcome === "paused" || outcome === "offline") {
            if (outcome === "offline") setSaveState("offline");
            scheduleRetry();
            return;
          }
        }
      }
      setSaveState("saved");
    } finally {
      flushingRef.current = false;
    }
  }, [attemptId, handleRejected, scheduleRetry]);

  useEffect(() => { flushRef.current = flush; }, [flush]);

  useEffect(() => {
    window.addEventListener("online", flush);
    return () => window.removeEventListener("online", flush);
  }, [flush]);

  function enqueue(questionId, patch) {
    const previous = queueRef.current.get(questionId) || { question_id: questionId };
    queueRef.current.set(questionId, { ...previous, ...patch }); // new object each time
    flush();
  }

  // ---------------------------------------------------------------- submit
  const doSubmit = useCallback(async (force = false) => {
    if (submittingRef.current || finishedRef.current) return;
    submittingRef.current = true;
    setSubmitting(true);
    setNotice("");
    try {
      // 1. make sure every answer reached the server
      for (let i = 0; i < 8 && queueRef.current.size > 0; i += 1) {
        await flush();
        if (queueRef.current.size > 0) await sleep(500);
      }
      if (queueRef.current.size > 0 && !force) {
        setNotice("Some answers could not be saved yet. Check your connection and press Submit again.");
        return;
      }
      // 2. submit. When time is up we keep trying; the server also grades expired attempts by itself.
      for (;;) {
        try {
          await submitAttempt(attemptId);
          goToResult();
          return;
        } catch (err) {
          if (!force) {
            setNotice(isNetworkError(err) ? "No connection. Please try again." : err.message || "Could not submit.");
            return;
          }
          if (!mountedRef.current) return;
          try {
            if (!applyServerState(await fetchAttempt(attemptId))) return;
          } catch (checkError) { /* still offline: try again below */ }
          await sleep(3000);
        }
      }
    } finally {
      submittingRef.current = false;
      if (mountedRef.current) setSubmitting(false);
    }
  }, [attemptId, flush, goToResult, applyServerState]);

  // ---------------------------------------------------------------- clock + server sync
  useEffect(() => {
    if (!exam) return undefined;
    const tick = () => {
      const left = Math.max(0, Math.ceil((endAtRef.current - Date.now()) / 1000));
      setRemaining(left);
      if (left === 0 && !submittingRef.current && !finishedRef.current) {
        setConfirmOpen(false);
        setNotice("Time is up. Submitting your exam...");
        doSubmit(true);
      }
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [exam, doSubmit]);

  useEffect(() => {
    if (!exam) return undefined;
    const delay = status === "FROZEN" ? 5000 : 20000;
    const id = setInterval(async () => {
      try {
        const view = await fetchAttempt(attemptId);
        if (applyServerState(view) && view.status === "ACTIVE") flush();
      } catch (err) { /* offline: the next tick will try again */ }
    }, delay);
    return () => clearInterval(id);
  }, [exam, status, attemptId, applyServerState, flush]);

  useEffect(() => {
    if (!exam) return undefined;
    const warn = (e) => { e.preventDefault(); e.returnValue = ""; };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [exam]);

  // ---------------------------------------------------------------- render
  if (loadError) {
    return (
      <div className="st-fullpage">
        <div className="st-panel narrow">
          <div className="st-alert danger">{loadError}</div>
          <button type="button" className="st-btn secondary" onClick={() => navigate("/student", { replace: true })}>
            Back to my exams
          </button>
        </div>
      </div>
    );
  }
  if (!exam) return <div className="st-fullpage"><p className="st-muted">Loading your exam...</p></div>;

  const { questions } = exam;
  const q = questions[current];
  const counts = summarize(questions, answers, marked);
  const frozen = status === "FROZEN";
  const locked = frozen || submitting;
  const tone = timerTone(remaining ?? 0);

  function choose(key) {
    if (locked) return;
    setAnswers((prev) => ({ ...prev, [q.id]: key }));
    enqueue(q.id, { question_id: q.id, selected_option: key });
  }

  function clearAnswer() {
    if (locked || !answers[q.id]) return;
    setAnswers((prev) => ({ ...prev, [q.id]: null }));
    enqueue(q.id, { question_id: q.id, selected_option: null });
  }

  function toggleReview() {
    if (locked) return;
    const next = !marked[q.id];
    setMarked((prev) => ({ ...prev, [q.id]: next }));
    enqueue(q.id, { question_id: q.id, marked_for_review: next });
  }

  return (
    <div className="st-exam">
      <header className="st-exam-bar">
        <div className="st-exam-title">
          <strong>{exam.name}</strong>
          <span>Question {current + 1} of {questions.length}</span>
        </div>
        <div className={`st-save ${saveState}`} role="status">{SAVE_TEXT[saveState]}</div>
        <div className={`st-timer ${tone}`} aria-label="Time left">
          <span>Time left</span>
          <strong>{formatClock(remaining ?? 0)}</strong>
        </div>
        <button type="button" className="st-btn primary" disabled={locked} onClick={() => setConfirmOpen(true)}>
          Submit exam
        </button>
      </header>

      {notice && <div className="st-alert warn st-exam-notice">{notice}</div>}

      <div className="st-exam-body">
        <section className="st-question">
          <div className="st-question-meta">
            <span>Question {current + 1}</span>
            <span className="st-chip info">{q.marks} {q.marks === 1 ? "mark" : "marks"}</span>
            {marked[q.id] && <span className="st-chip warn">Marked for review</span>}
          </div>
          <p className="st-question-text">{q.text}</p>

          <div className="st-options" role="radiogroup" aria-label="Answer options">
            {q.options.map((option, index) => (
              <button
                key={option.key}
                type="button"
                role="radio"
                aria-checked={answers[q.id] === option.key}
                className={`st-option ${answers[q.id] === option.key ? "selected" : ""}`}
                disabled={locked}
                onClick={() => choose(option.key)}
              >
                <span className="st-option-letter">{LETTERS[index]}</span>
                <span>{option.text}</span>
              </button>
            ))}
          </div>

          <div className="st-question-actions">
            <button type="button" className="st-btn secondary" disabled={current === 0} onClick={() => setCurrent(current - 1)}>
              Previous
            </button>
            <button type="button" className="st-btn ghost" disabled={locked || !answers[q.id]} onClick={clearAnswer}>
              Clear answer
            </button>
            <button type="button" className={`st-btn ${marked[q.id] ? "warn" : "ghost"}`} disabled={locked} onClick={toggleReview}>
              {marked[q.id] ? "Unmark review" : "Mark for review"}
            </button>
            {current < questions.length - 1 ? (
              <button type="button" className="st-btn primary" onClick={() => setCurrent(current + 1)}>Next</button>
            ) : (
              <button type="button" className="st-btn primary" disabled={locked} onClick={() => setConfirmOpen(true)}>
                Review and submit
              </button>
            )}
          </div>
        </section>

        <aside className="st-palette">
          <h3>Questions</h3>
          <div className="st-palette-grid">
            {questions.map((item, index) => (
              <button
                key={item.id}
                type="button"
                className={`st-pal ${questionState(answers[item.id], marked[item.id])} ${index === current ? "current" : ""}`}
                onClick={() => setCurrent(index)}
                aria-label={`Question ${index + 1}`}
              >
                {index + 1}
              </button>
            ))}
          </div>
          <ul className="st-legend">
            <li><i className="st-dot answered" /> Answered ({counts.answered})</li>
            <li><i className="st-dot unanswered" /> Not answered ({counts.unanswered})</li>
            <li><i className="st-dot review" /> Marked for review ({counts.review})</li>
          </ul>
        </aside>
      </div>

      {confirmOpen && (
        <div className="st-modal-backdrop" role="dialog" aria-modal="true" aria-label="Submit exam">
          <div className="st-modal">
            <h3>Submit your exam?</h3>
            <div className="st-tiles">
              <div><strong>{counts.answered}</strong><span>Answered</span></div>
              <div className={counts.unanswered ? "bad" : ""}><strong>{counts.unanswered}</strong><span>Not answered</span></div>
              <div className={counts.review ? "warn" : ""}><strong>{counts.review}</strong><span>For review</span></div>
            </div>
            {counts.unanswered > 0 && <p className="st-hint">You still have unanswered questions. They will be marked as not answered.</p>}
            <p className="st-hint">After you submit you cannot change your answers.</p>
            <div className="st-actions">
              <button type="button" className="st-btn secondary" disabled={submitting} onClick={() => setConfirmOpen(false)}>
                Go back
              </button>
              <button
                type="button"
                className="st-btn primary"
                disabled={submitting}
                onClick={() => { setConfirmOpen(false); doSubmit(false); }}
              >
                {submitting ? "Submitting..." : "Yes, submit"}
              </button>
            </div>
          </div>
        </div>
      )}

      {frozen && (
        <div className="st-modal-backdrop frozen" role="alertdialog" aria-modal="true">
          <div className="st-modal">
            <h3>Your exam is paused</h3>
            <p>The invigilator has paused this attempt. Please wait and do not close this page. It will continue automatically when the exam is resumed.</p>
            <p className="st-hint">Time left: {formatClock(remaining ?? 0)}</p>
          </div>
        </div>
      )}
    </div>
  );
}
