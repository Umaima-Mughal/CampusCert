import { apiRequest } from "./client";

// Examiner: marks of every student for one exam
export function getExamStudentResults(examId) {
  return apiRequest(
    `/api/analytics/exams/${examId}/results`
  );
}
