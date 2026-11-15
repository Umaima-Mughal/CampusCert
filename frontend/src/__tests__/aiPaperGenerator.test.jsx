// @vitest-environment jsdom
/** AI paper generator tab (examiner side), with the backend replaced by mocks. */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/react";

vi.mock("../api/aiPaper", () => ({ getAiStatus: vi.fn(), generateAiPaper: vi.fn() }));
import { getAiStatus, generateAiPaper } from "../api/aiPaper";
import AiPaperGenerator from "../questionbank/AiPaperGenerator";

beforeEach(() => { cleanup(); vi.clearAllMocks(); getAiStatus.mockResolvedValue({ configured: true, model: "m", max_questions: 40 }); });

const type = (text) => fireEvent.change(screen.getByRole("textbox", { name: /what should the paper contain/i }), { target: { value: text } });

describe("AiPaperGenerator", () => {
  it("needs a prompt before the button works", async () => {
    render(<AiPaperGenerator onCreated={() => {}} />);
    const btn = screen.getByRole("button", { name: /create paper with ai/i });
    expect(btn.disabled).toBe(true);
    type("20 MCQs on Operating Systems");
    expect(btn.disabled).toBe(false);
  });

  it("sends only the prompt and opens the finished paper", async () => {
    const paper = { id: 7, title: "OS", question_count: 20, warnings: [] };
    generateAiPaper.mockResolvedValue(paper);
    const onCreated = vi.fn();
    render(<AiPaperGenerator onCreated={onCreated} />);
    type("20 MCQs on Operating Systems");
    fireEvent.click(screen.getByRole("button", { name: /create paper with ai/i }));
    await waitFor(() => expect(onCreated).toHaveBeenCalledWith(paper));
    expect(generateAiPaper).toHaveBeenCalledWith({ prompt: "20 MCQs on Operating Systems" });
  });

  it("passes the optional question count", async () => {
    generateAiPaper.mockResolvedValue({ id: 1, warnings: [] });
    render(<AiPaperGenerator onCreated={() => {}} />);
    type("10 MCQs on Algebra please");
    fireEvent.change(screen.getByLabelText(/number of questions/i), { target: { value: "12" } });
    fireEvent.click(screen.getByRole("button", { name: /create paper with ai/i }));
    await waitFor(() => expect(generateAiPaper).toHaveBeenCalledWith({ prompt: "10 MCQs on Algebra please", question_count: 12 }));
  });

  it("shows the error and lets the examiner retry", async () => {
    generateAiPaper.mockRejectedValue(new Error("The free AI limit was reached."));
    render(<AiPaperGenerator onCreated={() => {}} />);
    type("20 MCQs on Operating Systems");
    fireEvent.click(screen.getByRole("button", { name: /create paper with ai/i }));
    expect(await screen.findByText(/free AI limit/)).toBeTruthy();
    expect(screen.getByRole("button", { name: /create paper with ai/i }).disabled).toBe(false);
  });

  it("shows warnings first when the AI could not write every question", async () => {
    const paper = { id: 3, title: "Net", question_count: 8, warnings: ["The AI could only write 8 valid question(s) of the 10 planned."] };
    generateAiPaper.mockResolvedValue(paper);
    const onCreated = vi.fn();
    render(<AiPaperGenerator onCreated={onCreated} />);
    type("10 MCQs on Networks");
    fireEvent.click(screen.getByRole("button", { name: /create paper with ai/i }));
    expect(await screen.findByText(/could only write 8/)).toBeTruthy();
    expect(onCreated).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: /open the paper/i }));
    expect(onCreated).toHaveBeenCalledWith(paper);
  });

  it("explains how to set up the key when it is missing", async () => {
    getAiStatus.mockResolvedValue({ configured: false, model: "m", max_questions: 40 });
    render(<AiPaperGenerator onCreated={() => {}} />);
    expect(await screen.findByText(/GROQ_API_KEY/)).toBeTruthy();
    type("20 MCQs on Operating Systems");
    expect(screen.getByRole("button", { name: /create paper with ai/i }).disabled).toBe(true);
  });
});
