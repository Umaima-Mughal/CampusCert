import { useEffect, useState } from "react";
import { generatePaper, getFilterOptions } from "../api/questionsApi";

const DIFFS = ["easy", "medium", "hard"];
const cap = (s) => s[0].toUpperCase() + s.slice(1);
const num = (v) => Math.max(0, parseInt(v, 10) || 0);

// Pick random questions from the teacher's filters and create the paper in one click.
export default function PaperGenerator({ onCreated }) {
  const [options, setOptions] = useState({ subjects: [], topics: [] });
  const [subject, setSubject] = useState("");
  const [topics, setTopics] = useState([]);          // none selected = all topics
  const [mode, setMode] = useState("any");           // any | one | mix
  const [difficulty, setDifficulty] = useState("easy");
  const [count, setCount] = useState(10);
  const [mix, setMix] = useState({ easy: 4, medium: 4, hard: 2 });
  const [title, setTitle] = useState("");
  const [duration, setDuration] = useState("");
  const [instructions, setInstructions] = useState("");
  const [marksEach, setMarksEach] = useState(1);
  const [partial, setPartial] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getFilterOptions(subject)
      .then((o) => { setOptions(o); setTopics((t) => t.filter((x) => o.topics.includes(x))); })
      .catch(() => {});
  }, [subject]);

  const mixTotal = DIFFS.reduce((s, d) => s + mix[d], 0);
  const wanted = mode === "mix" ? mixTotal : num(count);
  const canGenerate = title.trim() && wanted >= 1 && wanted <= 200 && !loading;
  const toggleTopic = (t) => setTopics((cur) => (cur.includes(t) ? cur.filter((x) => x !== t) : [...cur, t]));

  async function generate() {
    setLoading(true); setError("");
    const body = {
      title: title.trim(), instructions: instructions.trim() || null,
      duration_minutes: duration === "" ? null : Number(duration),
      marks_each: Math.max(1, num(marksEach)), allow_partial: partial,
      subject: subject || null, topics,
    };
    if (mode === "mix") body.mix = mix;
    else { body.count = num(count); if (mode === "one") body.difficulty = difficulty; }
    try { onCreated(await generatePaper(body)); }
    catch (e) { setError(e.message); setLoading(false); }
  }

  return (
    <div className="qb-body">
      <aside className="qb-filters" aria-label="Where to pick questions from">
        <h2 className="qb-h2">Pick questions from</h2>
        <label>Subject
          <select value={subject} onChange={(e) => setSubject(e.target.value)}>
            <option value="">All subjects</option>
            {options.subjects.map((s) => <option key={s}>{s}</option>)}
          </select>
        </label>

        <fieldset>
          <legend>Topics {topics.length === 0 ? "(all)" : `(${topics.length} chosen)`}</legend>
          <div className="qb-topics">
            {options.topics.map((t) => (
              <button key={t} type="button" aria-pressed={topics.includes(t)} onClick={() => toggleTopic(t)}>{t}</button>
            ))}
            {options.topics.length === 0 && <span className="qb-hint">No topics yet. Upload a file first.</span>}
          </div>
        </fieldset>

        <fieldset>
          <legend>Difficulty</legend>
          <div className="qb-seg qb-seg--3">
            {[["any", "Any"], ["one", "One level"], ["mix", "Mix"]].map(([m, label]) => (
              <button key={m} type="button" aria-pressed={mode === m} onClick={() => setMode(m)}>{label}</button>
            ))}
          </div>
        </fieldset>

        {mode === "one" && (
          <label>Level
            <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
              {DIFFS.map((d) => <option key={d} value={d}>{cap(d)}</option>)}
            </select>
          </label>
        )}

        {mode === "mix" ? (
          <>
            <div className="qb-mix">
              {DIFFS.map((d) => (
                <label key={d}>{cap(d)}
                  <input type="number" min="0" max="200" value={mix[d]} onChange={(e) => setMix({ ...mix, [d]: num(e.target.value) })} />
                </label>
              ))}
            </div>
            <p className="qb-hint">Total: {mixTotal} question{mixTotal === 1 ? "" : "s"}</p>
          </>
        ) : (
          <label>How many questions
            <input type="number" min="1" max="200" value={count} onChange={(e) => setCount(e.target.value)} />
          </label>
        )}
      </aside>

      <main className="qb-results">
        <div className="qb-card">
          <h2 className="qb-h2">Exam paper details</h2>
          {error && <p className="qb-error" role="alert">{error}</p>}
          <div className="qb-form">
            <label>Paper title
              <input value={title} maxLength={200} placeholder="e.g. Physics midterm" onChange={(e) => setTitle(e.target.value)} />
            </label>
            <div className="qb-row">
              <label>Time allowed (minutes)
                <input type="number" min="1" max="600" value={duration} placeholder="optional" onChange={(e) => setDuration(e.target.value)} />
              </label>
              <label>Marks per question
                <input type="number" min="1" max="100" value={marksEach} onChange={(e) => setMarksEach(e.target.value)} />
              </label>
            </div>
            <label>Instructions for students
              <textarea rows={3} value={instructions} placeholder="optional" onChange={(e) => setInstructions(e.target.value)} />
            </label>
            <label className="qb-check">
              <input type="checkbox" checked={partial} onChange={(e) => setPartial(e.target.checked)} />
              Create anyway if fewer questions match than I asked for
            </label>
            <button className="qb-btn qb-btn--primary" disabled={!canGenerate} onClick={generate}>
              {loading ? "Generating…" : "Generate exam paper"}
            </button>
            {!title.trim() && <p className="qb-hint">Give the paper a title to generate it.</p>}
            <p className="qb-hint">
              The questions are picked at random from the choices on the left. You can swap, remove or reorder
              them afterwards, or generate again for a different paper.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
