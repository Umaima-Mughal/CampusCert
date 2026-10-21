// Member 3's API calls.
// VITE_API_URL is shared with Member 1's src/api/client.js, which expects the
// plain server root (http://localhost:8000). So we strip any trailing /api/v1
// from it and add /api/v1 ourselves; this works whichever form the env uses.
const ROOT = (import.meta.env.VITE_API_URL || "http://localhost:8000")
  .replace(/\/+$/, "")
  .replace(/\/api\/v1$/, "");
const BASE = `${ROOT}/api/v1`;

async function handle(res) {
  if (res.ok) return res.status === 204 ? null : res.json();
  let msg = res.status === 401 || res.status === 403
    ? "Please log in as an admin or examiner to use the question bank."
    : "Something went wrong. Try again.";
  try {
    const d = (await res.json()).detail;
    if (typeof d === "string") msg = d;
    else if (Array.isArray(d)) msg = d.map((e) => e.msg).join("; ");
    else if (d && typeof d === "object" && d.message) {       // a rejected import file
      const err = new Error(d.message);
      err.errors = d.errors || [];
      err.totalErrors = d.total_errors || err.errors.length;
      throw err;
    }
  } catch (e) {
    if (e.errors) throw e;
    /* otherwise keep the default message */
  }
  throw new Error(msg);
}

// Same token Member 1's login stores (see api/client.js). Every question-bank route needs it now.
const authHeaders = () => {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const importQuestions = (file) => {
  const body = new FormData();
  body.append("file", file);
  return fetch(`${BASE}/questions/import`, { method: "POST", body, headers: authHeaders() }).then(handle);
};

export const listQuestions = (params) => {
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v));
  return fetch(`${BASE}/questions?${qs}`, { headers: authHeaders() }).then(handle);
};

export const getFilterOptions = (subject) =>
  fetch(`${BASE}/questions/filters${subject ? `?subject=${encodeURIComponent(subject)}` : ""}`,
        { headers: authHeaders() }).then(handle);

// body: { ids: [..] }  or  { all_matching: true, subject?, topic?, difficulty?, q? }  -> { deleted }
export const bulkDeleteQuestions = (body) =>
  fetch(`${BASE}/questions/bulk-delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  }).then(handle);

export const deleteQuestion = (id) =>
  fetch(`${BASE}/questions/${id}`, { method: "DELETE", headers: authHeaders() }).then(handle);

// ---- Exam papers ----
const json = (method, body) => ({
  method,
  headers: { "Content-Type": "application/json", ...authHeaders() },
  body: JSON.stringify(body),
});

// body: { title, instructions, duration_minutes, items: [{ question_id, marks }] }
export const createPaper = (body) => fetch(`${BASE}/questions/papers`, json("POST", body)).then(handle);
export const updatePaper = (id, body) => fetch(`${BASE}/questions/papers/${id}`, json("PUT", body)).then(handle);

// body: { title, instructions, duration_minutes, marks_each, allow_partial,
//         subject, topics[], difficulty | mix{easy,medium,hard}, count }
export const generatePaper = (body) => fetch(`${BASE}/questions/papers/generate`, json("POST", body)).then(handle);

export const listPapers = () => fetch(`${BASE}/questions/papers`, { headers: authHeaders() }).then(handle);
export const getPaper = (id) => fetch(`${BASE}/questions/papers/${id}`, { headers: authHeaders() }).then(handle);
export const deletePaper = (id) =>
  fetch(`${BASE}/questions/papers/${id}`, { method: "DELETE", headers: authHeaders() }).then(handle);

// Random questions. body: { subject?, topics[], difficulty?, count, exclude_ids[] }
export const pickRandom = (body) => fetch(`${BASE}/questions/random`, json("POST", body)).then(handle);
