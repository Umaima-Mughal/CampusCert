// @vitest-environment jsdom
/** Dashboard, instructions page and result page (Member 4), with the backend replaced by mocks. */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

vi.mock("../api/attempts", () => ({
  fetchMyExams: vi.fn(), fetchMyResults: vi.fn(), fetchExamInstructions: vi.fn(),
  startAttempt: vi.fn(), fetchResult: vi.fn(),
}));
vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({ user: { full_name: "Ayesha", role: "student" }, loading: false, logout: () => {} }),
}));
import { fetchMyExams, fetchMyResults, fetchExamInstructions, startAttempt, fetchResult } from "../api/attempts";
import StudentDashboard from "../student/StudentDashboard";
import InstructionsPage from "../student/InstructionsPage";
import ResultPage from "../student/ResultPage";

const exam = (o) => ({
  id: "e1", name: "Networks Midterm", description: "Ch 1-4", duration_minutes: 30, status: "ACTIVE",
  starts_at: null, ends_at: null, max_attempts: 1, attempts_used: 0, open_attempt_id: null, last_attempt_id: null,
  last_attempt_status: null, can_start: true, blocked_reason: null, ...o,
});

beforeEach(() => { cleanup(); vi.clearAllMocks(); fetchMyResults.mockResolvedValue([]); });

describe("dashboard", () => {
  const mount = () => render(
    <MemoryRouter initialEntries={["/student"]}>
      <Routes>
        <Route path="/student" element={<StudentDashboard />} />
        <Route path="/student/exam/:id" element={<div>INSTRUCTIONS</div>} />
        <Route path="/student/attempt/:id" element={<div>EXAM SCREEN</div>} />
        <Route path="/student/result/:id" element={<div>RESULT</div>} />
      </Routes>
    </MemoryRouter>
  );

  it("starts an open exam via the instructions page", async () => {
    fetchMyExams.mockResolvedValue([exam()]);
    mount();
    fireEvent.click(await screen.findByText("Start exam"));
    expect(await screen.findByText("INSTRUCTIONS")).toBeTruthy();
  });

  it("resumes an exam in progress", async () => {
    fetchMyExams.mockResolvedValue([exam({ open_attempt_id: "a9", attempts_used: 1 })]);
    mount();
    fireEvent.click(await screen.findByText("Resume exam"));
    expect(await screen.findByText("EXAM SCREEN")).toBeTruthy();
  });

  it("shows the result of a completed exam and why a blocked exam cannot start", async () => {
    fetchMyExams.mockResolvedValue([
      exam({ attempts_used: 1, can_start: false, last_attempt_id: "a1", last_attempt_status: "SUBMITTED",
             blocked_reason: "You have used all 1 attempt(s) for this exam." }),
      exam({ id: "e2", name: "Future exam", status: "SCHEDULED", can_start: false, blocked_reason: "This exam is not open." }),
    ]);
    mount();
    expect(await screen.findByText("Completed")).toBeTruthy();
    expect(screen.getByText("This exam is not open.")).toBeTruthy();
    fireEvent.click(screen.getByText("View result"));
    expect(await screen.findByText("RESULT")).toBeTruthy();
  });

  it("shows an empty state", async () => {
    fetchMyExams.mockResolvedValue([]);
    mount();
    expect(await screen.findByText("No exams yet")).toBeTruthy();
  });
});

describe("instructions", () => {
  const mount = () => render(
    <MemoryRouter initialEntries={["/student/exam/e1"]}>
      <Routes>
        <Route path="/student/exam/:examId" element={<InstructionsPage />} />
        <Route path="/student/attempt/:id" element={<div>EXAM SCREEN</div>} />
      </Routes>
    </MemoryRouter>
  );
  beforeEach(() => fetchExamInstructions.mockResolvedValue({
    id: "e1", name: "Networks Midterm", description: "", instructions: "Bring no notes.",
    duration_minutes: 30, question_count: 20, passing_score: 50, max_attempts: 1, ends_at: null,
  }));

  it("only lets the student start after agreeing", async () => {
    startAttempt.mockResolvedValue({ attempt_id: "a1" });
    mount();
    const start = await screen.findByText("Start exam");
    expect(screen.getByText("Bring no notes.")).toBeTruthy();
    expect(start.disabled).toBe(true);
    fireEvent.click(screen.getByRole("checkbox"));
    expect(start.disabled).toBe(false);
    fireEvent.click(start);
    await waitFor(() => expect(startAttempt).toHaveBeenCalledWith("e1"));
    expect(await screen.findByText("EXAM SCREEN")).toBeTruthy();
  });

  it("shows the server reason when the exam cannot start", async () => {
    startAttempt.mockRejectedValue(new Error("The exam window has closed."));
    mount();
    fireEvent.click(await screen.findByRole("checkbox"));
    fireEvent.click(screen.getByText("Start exam"));
    expect(await screen.findByText("The exam window has closed.")).toBeTruthy();
  });
});

describe("result", () => {
  const result = {
    attempt_id: "a1", exam_name: "Networks Midterm", attempt_number: 1, status: "SUBMITTED",
    submitted_at: "2026-10-19T10:00:00", total_marks: 3, obtained_marks: 1, correct_count: 1,
    incorrect_count: 1, unanswered_count: 1, percentage: 33.33, passed: false, passing_score: 50,
    breakdown: [
      { question_id: 1, position: 1, marks: 1, selected: "B", correct: "B", awarded: 1, gradable: true, question: "Q one", options: { A: "a1", B: "b1" } },
      { question_id: 2, position: 2, marks: 1, selected: "A", correct: "B", awarded: 0, gradable: true, question: "Q two", options: { A: "a2", B: "b2" } },
      { question_id: 3, position: 3, marks: 1, selected: null, correct: "A", awarded: 0, gradable: true, question: "Q three", options: { A: "a3", B: "b3" } },
    ],
  };
  const mount = () => render(
    <MemoryRouter initialEntries={["/student/result/a1"]}>
      <Routes><Route path="/student/result/:attemptId" element={<ResultPage />} /></Routes>
    </MemoryRouter>
  );

  it("shows score, pass/fail and filters the review", async () => {
    fetchResult.mockResolvedValue(result);
    mount();
    expect(await screen.findByText("You did not reach the pass mark")).toBeTruthy();
    expect(screen.getByText("33.3%")).toBeTruthy();
    expect(screen.getByText("1 / 3 marks")).toBeTruthy();
    fireEvent.click(screen.getByRole("tab", { name: "Incorrect" }));
    expect(screen.getByText("Q two")).toBeTruthy();
    expect(screen.queryByText("Q one")).toBeNull();
    fireEvent.click(screen.getByRole("tab", { name: "Not answered" }));
    expect(screen.getByText("Q three")).toBeTruthy();
  });

  it("explains when the result is not ready", async () => {
    fetchResult.mockRejectedValue(new Error("This attempt has not been submitted yet."));
    mount();
    expect(await screen.findByText("This attempt has not been submitted yet.")).toBeTruthy();
  });

  it("hides correct answers when the server withholds them", async () => {
    fetchResult.mockResolvedValue({ ...result, breakdown: result.breakdown.map((b) => ({ ...b, correct: null })) });
    mount();
    await screen.findByText("Q one");
    expect(screen.queryByText("Correct answer")).toBeNull();
  });
});
