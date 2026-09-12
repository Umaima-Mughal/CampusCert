// Shared API client — owned by Member 1.
// Add your module's calls in your own file in this folder
// (e.g. api/exams.js, api/questions.js) — don't edit this base client
// without a heads-up, it's shared by every module.
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}
