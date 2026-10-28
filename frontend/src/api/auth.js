
/**
 * src/api/auth.js
 *
 * All API calls related to authentication.
 * This is Member 1's own file inside the shared src/api/ folder —
 * other members add THEIR OWN files here for their own modules
 * (e.g. src/api/exams.js for Member 2), instead of editing this one.
 */

import { apiRequest, setTokens, clearTokens } from "./client";

export async function registerUser({ fullName, email, password, role, orgCode, organizationId }) {
  return apiRequest(
    "/api/auth/register",
    {
      method: "POST",
      body: JSON.stringify({
        full_name: fullName,
        email,
        password,
        role: role || "student",
        org_code: orgCode,
        organization_id: organizationId || null,
      }),
    },
    false // no auth token needed to register
  );
}

export async function loginUser({ email, password }) {
  const tokens = await apiRequest(
    "/api/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ email, password }),
    },
    false // no auth token needed to log in
  );
  setTokens(tokens);
  return tokens;
}

export async function getCurrentUser() {
  return apiRequest("/api/auth/me", { method: "GET" });
}

export function logoutUser() {
  clearTokens();
}