/**
 * src/api/attempts.js
 *
 * Member 4 API calls for the student portal: dashboard, attempts, autosave,
 * submit and results. Built on the shared apiRequest helper (does not edit client.js).
 *
 * Note: apiRequest throws a plain Error (with the server message) when the server
 * answers with an error, and a TypeError when the network itself failed. The exam
 * screen relies on that difference to decide between "retry later" and "server said no".
 */
import { apiRequest } from "./client";

export function fetchMyExams() {
  return apiRequest("/api/attempts/my-exams", { method: "GET" });
}

export function fetchExamInstructions(examId) {
  return apiRequest(`/api/attempts/exams/${examId}`, { method: "GET" });
}

export function startAttempt(examId) {
  return apiRequest("/api/attempts/start", {
    method: "POST",
    body: JSON.stringify({ exam_id: examId }),
  });
}

export function fetchAttempt(attemptId) {
  return apiRequest(`/api/attempts/${attemptId}`, { method: "GET" });
}

/** body: { question_id, selected_option?: "A"-"D" | null, marked_for_review?: boolean } */
export function saveAnswer(attemptId, body) {
  return apiRequest(`/api/attempts/${attemptId}/answers`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function submitAttempt(attemptId) {
  return apiRequest(`/api/attempts/${attemptId}/submit`, { method: "POST" });
}

export function fetchResult(attemptId) {
  return apiRequest(`/api/results/${attemptId}`, { method: "GET" });
}

export function fetchMyResults() {
  return apiRequest("/api/results/mine", { method: "GET" });
}
