import { Route, Routes } from "react-router-dom";
import StudentGuard from "./StudentGuard";
import StudentLayout from "./StudentLayout";
import StudentDashboard from "./StudentDashboard";
import InstructionsPage from "./InstructionsPage";
import ExamPage from "./ExamPage";
import ResultPage from "./ResultPage";

/**
 * /student                       dashboard (my exams + my results)
 * /student/exam/:examId          instructions page, then start
 * /student/attempt/:attemptId    the exam itself (full screen, no menu, to avoid distractions)
 * /student/result/:attemptId     score and review
 */
export default function StudentRoutes() {
  return (
    <Routes>
      <Route element={<StudentGuard><StudentLayout /></StudentGuard>}>
        <Route index element={<StudentDashboard />} />
        <Route path="exam/:examId" element={<InstructionsPage />} />
        <Route path="result/:attemptId" element={<ResultPage />} />
      </Route>
      <Route path="attempt/:attemptId" element={<StudentGuard><ExamPage /></StudentGuard>} />
    </Routes>
  );
}
