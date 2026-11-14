import { apiRequest } from "./client";

// Member 5: Student integrity reporting
export function reportIntegrityEvent(attemptId, type) {
  return apiRequest("/api/events", {
    method: "POST",
    body: JSON.stringify({
      attempt_id: attemptId,
      type,
    }),
  });
}

// Examiner actions
export function resumeExamAttempt(attemptId, reason) {
  return apiRequest(`/api/attempts/${attemptId}/resume`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export function terminateExamAttempt(attemptId, reason) {
  return apiRequest(`/api/attempts/${attemptId}/terminate`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

// Examiner analytics
export function getExamSecurityOverview(examId) {
  return apiRequest(
    `/api/analytics/exams/${examId}/overview`
  );
}

export function getAttemptSecurityTimeline(attemptId) {
  return apiRequest(
    `/api/analytics/attempts/${attemptId}/timeline`
  );
}


export function getSecurityReviewQueue(examId) {
  return apiRequest(
    `/api/analytics/exams/${examId}/review-queue`
  );
}
