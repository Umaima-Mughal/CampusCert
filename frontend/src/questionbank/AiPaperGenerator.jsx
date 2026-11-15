import { useEffect, useState } from "react";
import { generateAiPaper, getAiStatus } from "../api/aiPaper";

const EXAMPLES = [
  "20 MCQs on Operating Systems: 40% easy, 40% medium, 20% hard",
  "15 medium-level MCQs on Python loops and functions for first-year students",
  "10 hard MCQs on Calculus: limits, derivatives and integrals",
  "25 MCQs on Computer Networks covering OSI model, TCP/IP and routing",
];

// The examiner only writes a prompt. The AI writes the questions, saves them in this examiner's own
// question bank and builds the exam paper, which then opens in "Exam papers" for review and editing.
export default function AiPaperGenerator({ onCreated }) {
  const [status, setStatus] = useState(null);       // { configured, model, max_questions } | null
  const [prompt, setPrompt] = useState("");
  const [count, setCount] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);       // a paper that came back with warnings

  useEffect(() => { getAiStatus().then(setStatus).catch(() => {}); }, []);

  const canGo = prompt.trim().length >= 8 && !loading && status?.configured !== false;

  async function generate() {
    setLoading(true); setError(""); setResult(null);
    const body = { prompt: prompt.trim() };
    if (count !== "") body.question_count = Math.max(1, parseInt(count, 10) || 1);
    try {
      const paper = await generateAiPaper(body);
      if (paper.warnings?.length) { setResult(paper); setLoading(false); }
      else onCreated(paper);
    } catch (e) { setError(e.message); setLoading(false); }
  }

  return (
    <div className="qb-card" style={{ maxWidth: 760 }}>
      <h2 className="qb-h2">Create an exam paper with AI</h2>
      <p className="qb-hint">
        Describe the paper you want. The AI writes every question with four options, the correct answer and a
        solution, and saves them in your question bank as a ready exam paper.
      </p>

      {status && !status.configured && (
        <p className="qb-error" role="alert">
          AI is not set up yet. Add your free Groq key as <code>GROQ_API_KEY</code> in the <code>.env</code> file
          (get one at console.groq.com/keys), then restart the backend.
        </p>
      )}
      {error && <p className="qb-error" role="alert">{error}</p>}

      <div className="qb-form">
        <label>What should the paper contain?
          <textarea rows={5} value={prompt} maxLength={2000} disabled={loading}
                    placeholder="e.g. 20 MCQs on Operating Systems: process scheduling, deadlocks and memory management. 40% easy, 40% medium, 20% hard."
                    onChange={(e) => setPrompt(e.target.value)} />
        </label>

        <div className="qb-topics" aria-label="Example prompts">
          {EXAMPLES.map((ex) => (
            <button key={ex} type="button" disabled={loading} onClick={() => setPrompt(ex)}>{ex}</button>
          ))}
        </div>

        <label>Number of questions (optional)
          <input type="number" min="1" max={status?.max_questions || 40} value={count} disabled={loading}
                 placeholder="leave empty to use the number in your prompt"
                 onChange={(e) => setCount(e.target.value)} />
        </label>

        <button className="qb-btn qb-btn--primary" disabled={!canGo} onClick={generate}>
          {loading ? "AI is writing your paper…" : "Create paper with AI"}
        </button>
        {loading && <p className="qb-hint" role="status">This usually takes 10 to 40 seconds. Please keep this page open.</p>}
        {!loading && prompt.trim().length < 8 && <p className="qb-hint">Write at least a short sentence about the paper.</p>}
        <p className="qb-hint">
          AI can make mistakes. Open the paper afterwards and check the questions and answers before you use it in an exam.
        </p>
      </div>

      {result && (
        <section className="qb-note" role="status">
          <p><strong>Paper "{result.title}" was created with {result.question_count} question{result.question_count === 1 ? "" : "s"}.</strong></p>
          <ul>{result.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
          <button className="qb-btn qb-btn--primary" onClick={() => onCreated(result)}>Open the paper</button>
        </section>
      )}
    </div>
  );
}
