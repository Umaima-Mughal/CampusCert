/**
 * src/api/organizations.js
 *
 * Public onboarding + any org-related client calls for this phase.
 */

import { apiRequest } from "./client";

export function onboardOrganization({ name, contactEmail }) {
  return apiRequest(
    "/api/organizations/onboard",
    {
      method: "POST",
      body: JSON.stringify({
        name,
        contact_email: contactEmail,
      }),
    },
    false
  );
}
