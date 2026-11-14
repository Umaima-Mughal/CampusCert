import { describe, it, expect } from "vitest";
import {
  examBadge, formatClock, isNetworkError, parseServerDate, percentLabel,
  questionState, summarize, timerTone,
} from "../student/studentUtils";

describe("studentUtils", () => {
  it("formats the countdown clock", () => {
    expect(formatClock(0)).toBe("00:00");
    expect(formatClock(125)).toBe("02:05");
    expect(formatClock(3725)).toBe("1:02:05");
    expect(formatClock(-5)).toBe("00:00");
    expect(formatClock(undefined)).toBe("00:00");
  });

  it("changes the timer colour near the end", () => {
    expect(timerTone(1800)).toBe("ok");
    expect(timerTone(300)).toBe("warn");
    expect(timerTone(61)).toBe("warn");
    expect(timerTone(60)).toBe("danger");
    expect(timerTone(0)).toBe("danger");
  });

  it("reads server times without a zone as UTC", () => {
    expect(parseServerDate("2026-10-19T10:00:00").toISOString()).toBe("2026-10-19T10:00:00.000Z");
    expect(parseServerDate("2026-10-19T10:00:00Z").toISOString()).toBe("2026-10-19T10:00:00.000Z");
    expect(parseServerDate("2026-10-19T15:00:00+05:00").toISOString()).toBe("2026-10-19T10:00:00.000Z");
    expect(parseServerDate(null)).toBeNull();
    expect(parseServerDate("not a date")).toBeNull();
  });

  it("works out the state of a question in the palette", () => {
    expect(questionState("A", false)).toBe("answered");
    expect(questionState(null, false)).toBe("unanswered");
    expect(questionState("A", true)).toBe("review");
    expect(questionState(null, true)).toBe("review");
  });

  it("counts answered, unanswered and review questions", () => {
    const questions = [{ id: 1 }, { id: 2 }, { id: 3 }];
    expect(summarize(questions, { 1: "A", 2: null }, { 2: true, 3: true })).toEqual({
      total: 3, answered: 1, unanswered: 2, review: 2,
    });
  });

  it("tells a network failure from a server answer", () => {
    expect(isNetworkError(new TypeError("Failed to fetch"))).toBe(true);
    expect(isNetworkError(new Error("Attempt is FROZEN"))).toBe(false);
  });

  it("labels exam cards", () => {
    expect(examBadge({ open_attempt_id: "x" }).label).toBe("In progress");
    expect(examBadge({ can_start: true, attempts_used: 0 }).label).toBe("Open");
    expect(examBadge({ can_start: false, attempts_used: 1 }).label).toBe("Completed");
    expect(examBadge({ can_start: false, attempts_used: 0, status: "SCHEDULED" }).label).toBe("Upcoming");
    expect(examBadge({ can_start: false, attempts_used: 0, status: "CLOSED" }).label).toBe("Closed");
  });

  it("formats percentages", () => {
    expect(percentLabel(50)).toBe("50%");
    expect(percentLabel(66.666)).toBe("66.7%");
    expect(percentLabel("x")).toBe("-");
  });
});
