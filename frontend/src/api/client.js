/**
 * src/api/client.js
 *
 * The ONE shared place that knows how to talk to the backend.
 * Everyone else (exams, questions, attempts, etc.) should build on top
 * of `apiRequest` in their OWN file inside this folder — e.g.
 * src/api/exams.js — rather than editing this file directly.
 *
 * Reads the backend URL from an environment variable so it's easy to
 * point at localhost during development and a real server later.
 */

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getAccessToken() {
  return localStorage.getItem("access_token");
}

function getRefreshToken() {
  return localStorage.getItem("refresh_token");
}

export function setTokens({ access_token, refresh_token }) {
  localStorage.setItem("access_token", access_token);
  localStorage.setItem("refresh_token", refresh_token);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

/**
 * Core request helper.
 *
 * @param {string} path - e.g. "/api/auth/login"
 * @param {object} options - fetch options (method, body, etc.)
 * @param {boolean} auth - attach the Authorization header if true (default)
 */
export async function apiRequest(path, options = {}, auth = true) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (auth) {
    const token = getAccessToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  // Try to auto-refresh once on a 401, then retry the original request.
  if (response.status === 401 && auth && getRefreshToken()) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      return apiRequest(path, options, auth);
    }
    clearTokens();
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    // some endpoints (e.g. DELETE) return no body — that's fine
  }

  if (!response.ok) {
    const message = (data && data.detail) || `Request failed (${response.status})`;
    throw new Error(message);
  }

  return data;
}

async function tryRefreshToken() {
  try {
    const res = await fetch(`${BASE_URL}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: getRefreshToken() }),
    });
    if (!res.ok) return false;
    const tokens = await res.json();
    setTokens(tokens);
    return true;
  } catch {
    return false;
  }
}
