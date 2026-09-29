import { Route, Routes } from "react-router-dom";
import AdminDashboard from "./AdminDashboard";
import AdminHome from "./AdminHome";
import ExamList from "./ExamList";
import ExamForm from "./ExamForm";
import ExamDetail from "./ExamDetail";

export default function AdminRoutes() {
  return (
    <Routes>
      <Route element={<AdminDashboard />}>
        <Route index element={<AdminHome />} />
        <Route path="exams" element={<ExamList />} />
        <Route path="exams/new" element={<ExamForm />} />
        <Route path="exams/:examId" element={<ExamDetail />} />
        <Route path="exams/:examId/edit" element={<ExamForm />} />
      </Route>
    </Routes>
  );
}
