// @vitest-environment jsdom
/**
 * The exam screen (Member 4): timer, autosave, offline retry, submit, auto-submit, frozen attempt.
 * The backend is replaced by mocks, so these tests need no server and no database.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

vi.mock("../api/attempts", () => ({
  fetchAttempt: vi.fn(),
  saveAnswer: vi.fn(),
  submitAttempt: vi.fn(),
}));
import { fetchAttempt, saveAnswer, submitAttempt } from "../api/attempts";
import ExamPage from "../student/ExamPage";

const view = (over = {}) => ({
  attempt_id: "a1", exam_id: "e1", exam_name: "Networks Midterm", status: "ACTIVE",
  remaining_seconds: 600,
  questions: [
    { id: 11, position: 1, text: "What is TCP?", marks: 1, selected: null, marked_for_review: false,
      options: [{ key: "C", text: "Transport protocol" }, { key: "A", text: "A cable" }, { key: "B", text: "A fruit" }, { key: "D", text: "A song" }] },
    { id: 12, position: 2, text: "What is UDP?", marks: 2, selected: "B", marked_for_review: true,
      options: [{ key: "A", text: "x" }, { key: "B", text: "y" }] },
  ],
  ...over,
});

function mount() {
  return render(
    <MemoryRouter initialEntries={["/student/attempt/a1"]}>
      <Routes>
        <Route path="/student/attempt/:attemptId" element={<ExamPage />} />
        <Route path="/student/result/:attemptId" element={<div>RESULT PAGE</div>} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  cleanup();
  vi.clearAllMocks();
  fetchAttempt.mockResolvedValue(view());
  saveAnswer.mockResolvedValue({ saved: true });
  submitAttempt.mockResolvedValue({ status: "SUBMITTED" });
});

describe("exam screen", () => {
  it("shows the question, the clock and restores saved answers", async () => {
    mount();
    expect(await screen.findByText("What is TCP?")).toBeTruthy();
    expect(screen.getByText("Networks Midterm")).toBeTruthy();
    expect(screen.getByText(/^(09|10):\d\d$/)).toBeTruthy();
    fireEvent.click(screen.getByLabelText("Question 2"));
    const selected = screen.getAllByRole("radio").find((r) => r.getAttribute("aria-checked") === "true");
    expect(selected.textContent).toContain("y");
    expect(screen.getByText("Marked for review")).toBeTruthy();
  });

  it("autosaves the chosen option straight away", async () => {
    mount();
    await screen.findByText("What is TCP?");
    fireEvent.click(screen.getByText("Transport protocol"));
    await waitFor(() => expect(saveAnswer).toHaveBeenCalledWith("a1", { question_id: 11, selected_option: "C" }));
    await waitFor(() => expect(screen.getByText("All answers saved")).toBeTruthy());
  });

  it("keeps the answer and retries when the connection drops", async () => {
    saveAnswer.mockRejectedValueOnce(new TypeError("Failed to fetch")).mockResolvedValue({ saved: true });
    mount();
    await screen.findByText("What is TCP?");
    fireEvent.click(screen.getByText("A cable"));
    await waitFor(() => expect(screen.getByText(/No connection/)).toBeTruthy());
    await waitFor(() => expect(saveAnswer).toHaveBeenCalledTimes(2), { timeout: 5000 });
    await waitFor(() => expect(screen.getByText("All answers saved")).toBeTruthy());
    expect(saveAnswer.mock.calls[1][1]).toEqual({ question_id: 11, selected_option: "A" });
  });

  it("saves a review flag and a cleared answer", async () => {
    mount();
    await screen.findByText("What is TCP?");
    fireEvent.click(screen.getByText("Mark for review"));
    await waitFor(() => expect(saveAnswer).toHaveBeenCalledWith("a1", { question_id: 11, marked_for_review: true }));
    fireEvent.click(screen.getByLabelText("Question 2"));
    fireEvent.click(screen.getByText("Clear answer"));
    await waitFor(() => expect(saveAnswer).toHaveBeenCalledWith("a1", { question_id: 12, selected_option: null }));
  });

  it("asks for confirmation, then submits and opens the result", async () => {
    mount();
    await screen.findByText("What is TCP?");
    fireEvent.click(screen.getByText("Transport protocol"));
    fireEvent.click(screen.getByText("Submit exam"));
    const dialog = await screen.findByRole("dialog");
    expect(dialog.textContent).toContain("Submit your exam?");
    expect(submitAttempt).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("Yes, submit"));
    await waitFor(() => expect(submitAttempt).toHaveBeenCalledWith("a1"));
    expect(await screen.findByText("RESULT PAGE")).toBeTruthy();
  });

  it("submits by itself when the time runs out", async () => {
    fetchAttempt.mockResolvedValue(view({ remaining_seconds: 2 }));
    mount();
    await screen.findByText("What is TCP?");
    await waitFor(() => expect(submitAttempt).toHaveBeenCalledWith("a1"), { timeout: 5000 });
    expect(await screen.findByText("RESULT PAGE")).toBeTruthy();
  });

  it("blocks answering and shows the pause message while frozen", async () => {
    fetchAttempt.mockResolvedValue(view({ status: "FROZEN" }));
    mount();
    expect(await screen.findByText("Your exam is paused")).toBeTruthy();
    fireEvent.click(screen.getByText("Transport protocol"));
    expect(saveAnswer).not.toHaveBeenCalled();
  });

  it("goes straight to the result if the attempt is already over", async () => {
    fetchAttempt.mockResolvedValue(view({ status: "SUBMITTED", questions: [] }));
    mount();
    expect(await screen.findByText("RESULT PAGE")).toBeTruthy();
  });

  it("shows why the exam could not load", async () => {
    fetchAttempt.mockRejectedValue(new Error("Attempt not found."));
    mount();
    expect(await screen.findByText("Attempt not found.")).toBeTruthy();
  });
});
