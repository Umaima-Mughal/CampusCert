/**
 * src/api/exams.js
 *
 * Member 2 API calls for exam management.
 * Built on the shared apiRequest helper — this file is the exam module's
 * own client, not an edit to auth.js or client.js.
 */

import { apiRequest } from "./client";

export function fetchExamSummary() {
  return apiRequest("/api/exams/summary", { method: "GET" });
}

export function fetchExams(status) {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiRequest(`/api/exams${query}`, { method: "GET" });
}

export function fetchExam(examId) {
  return apiRequest(`/api/exams/${examId}`, { method: "GET" });
}

export function createExam(payload) {
  return apiRequest("/api/exams", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateExam(examId, payload) {
  return apiRequest(`/api/exams/${examId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteExam(examId) {
  return apiRequest(`/api/exams/${examId}`, { method: "DELETE" });
}

export function scheduleExam(examId, payload) {
  return apiRequest(`/api/exams/${examId}/schedule`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function activateExam(examId) {
  return apiRequest(`/api/exams/${examId}/activate`, { method: "POST" });
}

export function deactivateExam(examId) {
  return apiRequest(`/api/exams/${examId}/deactivate`, { method: "POST" });
}

export function closeExam(examId) {
  return apiRequest(`/api/exams/${examId}/close`, { method: "POST" });
}

export function archiveExam(examId) {
  return apiRequest(`/api/exams/${examId}/archive`, { method: "POST" });
}

export function fetchEligibleCandidates() {
  return apiRequest("/api/exams/eligible-candidates", { method: "GET" });
}

export function fetchExamCandidates(examId) {
  return apiRequest(`/api/exams/${examId}/candidates`, { method: "GET" });
}

export function assignExamCandidates(examId, userIds) {
  return apiRequest(`/api/exams/${examId}/candidates`, {
    method: "POST",
    body: JSON.stringify({ user_ids: userIds }),
  });
}

export function removeExamCandidate(examId, userId) {
  return apiRequest(`/api/exams/${examId}/candidates/${userId}`, {
    method: "DELETE",
  });
}
