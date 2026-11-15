// AI paper generator (examiner side). Same server root and login token as questionsApi.js.
const ROOT = (import.meta.env.VITE_API_URL || "http://localhost:8000")
  .replace(/\/+$/, "")
  .replace(/\/api\/v1$/, "");
const BASE = `${ROOT}/api/v1`;

const authHeaders = () => {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

async function handle(res) {
  if (res.ok) return res.json();
  let msg = "Something went wrong. Try again.";
  if (res.status === 401 || res.status === 403) msg = "Please log in as an examiner to use the AI paper generator.";
  try {
    const d = (await res.json()).detail;
    if (typeof d === "string") msg = d;
    else if (Array.isArray(d)) msg = d.map((e) => e.msg).join("; ");
  } catch { /* keep the default message */ }
  throw new Error(msg);
}

// -> { configured, model, max_questions }
export const getAiStatus = () => fetch(`${BASE}/ai/status`, { headers: authHeaders() }).then(handle);

// body: { prompt, question_count?, title?, duration_minutes?, marks_each? }
// -> the finished paper (same shape as an exam paper) + { requested, skipped, ai_model, warnings[] }
export const generateAiPaper = (body) =>
  fetch(`${BASE}/ai/generate-paper`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  }).then(handle);
