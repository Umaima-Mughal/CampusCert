import { useEffect, useState } from "react";
import McqBlock from "./McqBlock";
import { createPaper, getFilterOptions, pickRandom, updatePaper } from "../api/questionsApi";

const DIFFS = ["easy", "medium", "hard"];
const cap = (s) => s[0].toUpperCase() + s.slice(1);

// "Change question": swap one question for a random one with the topic + difficulty the teacher picks.
// It never offers a question that is already in this paper.
function ChangeQuestion({ current, allIds, topics, onReplace }) {
  const [open, setOpen] = useState(false);
  const [topic, setTopic] = useState(current.topic);
  const [difficulty, setDifficulty] = useState(current.difficulty);
  const [tried, setTried] = useState([]);          // questions already offered here, so Find walks through new ones
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState({ kind: "", text: "" });

  const topicOptions = topics.includes(topic) ? topics : [topic, ...topics];
  const reset = () => { setTried([]); setMsg({ kind: "", text: "" }); };

  async function find() {
    setBusy(true); setMsg({ kind: "", text: "" });
    try {
      const r = await pickRandom({ topics: [topic], difficulty, count: 1, exclude_ids: [...allIds, ...tried] });
      if (r.items.length === 0) {
        setMsg({
          kind: "warn",
          text: tried.length
            ? `You have seen every ${difficulty} question in "${topic}" that isn't already in this paper.`
            : `There is no other ${difficulty} question in "${topic}" that isn't already in this paper.`,
        });
      } else {
        setTried((t) => [...t, current.id]);
        onReplace(r.items[0]);
        setMsg({ kind: "ok", text: "Question changed. Click Save changes to keep it." });
      }
    } catch (e) { setMsg({ kind: "error", text: e.message }); }
    finally { setBusy(false); }
  }

  return (
    <>
      <button className="qb-btn" aria-expanded={open} onClick={() => setOpen(!open)}>
        {open ? "Close" : "Change question"}
      </button>
      {open && (
        <div className="qb-change">
          <div className="qb-change-row">
            <label>Topic
              <select value={topic} onChange={(e) => { setTopic(e.target.value); reset(); }}>
                {topicOptions.map((t) => <option key={t}>{t}</option>)}
              </select>
            </label>
            <label>Difficulty
              <select value={difficulty} onChange={(e) => { setDifficulty(e.target.value); reset(); }}>
                {DIFFS.map((d) => <option key={d} value={d}>{cap(d)}</option>)}
              </select>
            </label>
            <button className="qb-btn qb-btn--primary" disabled={busy} onClick={find}>
              {busy ? "Finding…" : "Find a different question"}
            </button>
          </div>
          {msg.text && <p className={`qb-msg qb-msg--${msg.kind}`} role="status">{msg.text}</p>}
        </div>
      )}
    </>
  );
}

// Build or edit an exam paper. `paper` is set when editing; `initialItems` is [{ question, marks }].
export default function PaperEditor({ paper, initialItems, onSaved, onCancel }) {
  const [title, setTitle] = useState(paper?.title || "");
  const [instructions, setInstructions] = useState(paper?.instructions || "");
  const [duration, setDuration] = useState(paper?.duration_minutes ?? "");
  // each slot keeps a stable id, so a card keeps its open panel when its question is swapped
  const [items, setItems] = useState(() => initialItems.map((x, i) => ({ ...x, slot: i })));
  const [topics, setTopics] = useState([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { getFilterOptions().then((o) => setTopics(o.topics)).catch(() => {}); }, []);

  const total = items.reduce((s, x) => s + x.marks, 0);
  const canSave = title.trim() && items.length > 0 && !saving;
  const allIds = items.map((x) => x.question.id);

  const remove = (i) => setItems((cur) => cur.filter((_, k) => k !== i));
  const replace = (i, q) => setItems((cur) => cur.map((x, k) => (k === i ? { ...x, question: q } : x)));
  const setMarks = (i, v) =>
    setItems((cur) => cur.map((x, k) => (k === i ? { ...x, marks: Math.max(1, parseInt(v, 10) || 1) } : x)));

  async function save() {
    setSaving(true); setError("");
    const body = {
      title: title.trim(),
      instructions: instructions.trim() || null,
      duration_minutes: duration === "" ? null : Number(duration),
      items: items.map((x) => ({ question_id: x.question.id, marks: x.marks })),
    };
    try { onSaved(paper ? await updatePaper(paper.id, body) : await createPaper(body)); }
    catch (e) { setError(e.message); setSaving(false); }
  }

  return (
    <>
      <header className="qb-head">
        <h1>{paper ? "Edit exam paper" : "New exam paper"}</h1>
        <p>{items.length} question{items.length === 1 ? "" : "s"} · {total} mark{total === 1 ? "" : "s"} in total</p>
      </header>
      {error && <p className="qb-error" role="alert">{error}</p>}

      <div className="qb-body">
        <aside className="qb-filters" aria-label="Paper details">
          <label>Paper title
            <input value={title} maxLength={200} placeholder="e.g. Physics midterm" onChange={(e) => setTitle(e.target.value)} />
          </label>
          <label>Time allowed (minutes)
            <input type="number" min="1" max="600" value={duration} placeholder="optional"
                   onChange={(e) => setDuration(e.target.value)} />
          </label>
          <label>Instructions for students
            <textarea rows={4} value={instructions} placeholder="optional" onChange={(e) => setInstructions(e.target.value)} />
          </label>
          <button className="qb-btn qb-btn--primary qb-btn--block" disabled={!canSave} onClick={save}>
            {saving ? "Saving…" : paper ? "Save changes" : "Save exam paper"}
          </button>
          <button className="qb-btn qb-btn--block" onClick={onCancel}>Cancel</button>
          {!title.trim() && <p className="qb-hint">Give the paper a title to save it.</p>}
        </aside>

        <main className="qb-results">
          {items.length === 0 ? (
            <div className="qb-table-wrap"><div className="qb-empty">All questions were removed. Cancel and choose again.</div></div>
          ) : (
            <ol className="qb-picks">
              {items.map((x, i) => (
                <li key={x.slot} className="qb-pick">
                  <div className="qb-pick-meta">
                    <span className={`qb-chip qb-chip--${x.question.difficulty}`}>{x.question.difficulty}</span>
                    <span>{x.question.subject} · {x.question.topic}</span>
                  </div>
                  <p>{x.question.question}</p>
                  <McqBlock q={x.question} showAnswer />
                  <div className="qb-pick-tools">
                    <label className="qb-inline">Marks
                      <input type="number" min="1" max="100" value={x.marks} onChange={(e) => setMarks(i, e.target.value)} />
                    </label>
                    <ChangeQuestion current={x.question} allIds={allIds} topics={topics} onReplace={(q) => replace(i, q)} />
                    <button className="qb-link qb-link--danger" onClick={() => remove(i)}>Remove</button>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </main>
      </div>
    </>
  );
}
