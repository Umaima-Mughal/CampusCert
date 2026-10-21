const LETTERS = ["A", "B", "C", "D"];

/**
 * The four options of a multiple-choice question (Member 3).
 *   showAnswer: also mark the correct option and show the solution. Only examiners get these
 *               from the API; for admins the server leaves them empty.
 * Old questions imported before MCQ support have no options, so nothing is drawn for them.
 * Inline styles so it looks right inside both the question bank and the admin screens.
 */
export default function McqBlock({ q, showAnswer = false }) {
  if (!q || !q.option_a) return null;
  const options = [q.option_a, q.option_b, q.option_c, q.option_d];
  return (
    <div className="qb-mcq">
      <ul style={{ listStyle: "none", margin: "8px 0 0", padding: 0, display: "grid", gap: 4 }}>
        {options.map((text, i) => {
          const right = showAnswer && q.correct_option === LETTERS[i];
          return (
            <li
              key={LETTERS[i]}
              style={{ display: "flex", gap: 8, color: right ? "#34d399" : "inherit", fontWeight: right ? 600 : 400 }}
            >
              <span style={{ minWidth: 18 }}>{LETTERS[i]}.</span>
              <span>{text}{right ? "  ✓ correct" : ""}</span>
            </li>
          );
        })}
      </ul>
      {showAnswer && q.solution && (
        <p style={{ margin: "8px 0 0", opacity: 0.85 }}>
          <strong>Solution:</strong> {q.solution}
        </p>
      )}
    </div>
  );
}
