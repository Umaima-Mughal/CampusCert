/**
 * src/student/studentUtils.js  (Member 4)
 * Small pure helpers for the student portal, kept apart from the screens so they can be unit tested.
 */

/**
 * The backend stores times as UTC but sends them without a "Z" (for example
 * "2026-10-19T10:00:00"). new Date() would read that as LOCAL time, so add the Z first.
 */
export function parseServerDate(value) {
  if (!value) return null;
  const text = String(value);
  const hasZone = /(Z|[+-]\d{2}:?\d{2})$/.test(text);
  const date = new Date(hasZone ? text : `${text}Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDateTime(value) {
  const date = parseServerDate(value);
  return date ? date.toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "-";
}

const pad = (n) => String(n).padStart(2, "0");

/** 125 -> "02:05", 3725 -> "1:02:05" */
export function formatClock(totalSeconds) {
  const s = Math.max(0, Math.floor(Number(totalSeconds) || 0));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return h > 0 ? `${h}:${pad(m)}:${pad(sec)}` : `${pad(m)}:${pad(sec)}`;
}

/** Colour of the countdown: calm, then warning in the last 5 minutes, then danger in the last minute. */
export function timerTone(secondsLeft) {
  if (secondsLeft <= 60) return "danger";
  if (secondsLeft <= 300) return "warn";
  return "ok";
}

/** "answered" | "review" | "unanswered" for the question palette. */
export function questionState(selected, isMarked) {
  if (isMarked) return "review";
  return selected ? "answered" : "unanswered";
}

/** Counts shown in the submit confirmation. */
export function summarize(questions, answers, marked) {
  let answered = 0;
  let review = 0;
  for (const q of questions) {
    if (answers[q.id]) answered += 1;
    if (marked[q.id]) review += 1;
  }
  return { total: questions.length, answered, unanswered: questions.length - answered, review };
}

/** fetch() throws a TypeError when the network is down; server errors arrive as normal Errors. */
export function isNetworkError(err) {
  return err instanceof TypeError;
}

export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Badge shown on a dashboard exam card. */
export function examBadge(exam) {
  if (exam.open_attempt_id) return { label: "In progress", tone: "warn" };
  if (exam.attempts_used > 0 && !exam.can_start) return { label: "Completed", tone: "done" };
  if (exam.can_start) return { label: "Open", tone: "ok" };
  if (exam.status === "CLOSED") return { label: "Closed", tone: "muted" };
  if (exam.status === "SCHEDULED") return { label: "Upcoming", tone: "info" };
  return { label: "Not available", tone: "muted" };
}

export function percentLabel(value) {
  const n = Number(value);
  return Number.isFinite(n) ? `${Number.isInteger(n) ? n : n.toFixed(1)}%` : "-";
}
