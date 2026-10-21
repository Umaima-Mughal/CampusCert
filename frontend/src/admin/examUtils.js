export const EXAM_STATUSES = ["DRAFT", "SCHEDULED", "ACTIVE", "CLOSED", "ARCHIVED"];

export function statusLabel(status) {
  const labels = {
    DRAFT: "Draft",
    SCHEDULED: "Scheduled",
    ACTIVE: "Active",
    CLOSED: "Closed",
    ARCHIVED: "Archived",
  };
  return labels[status] || status;
}

export function formatDateTime(value) {
  if (!value) return "Not set";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not set";
  return date.toLocaleString();
}

export function toDateTimeLocal(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function toIsoOrNull(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString();
}

export function distributionEntries(distribution) {
  if (!distribution || typeof distribution !== "object") return [];
  return Object.entries(distribution).map(([subjectId, count]) => ({
    subjectId,
    count: String(count),
  }));
}

export function entriesToDistribution(entries) {
  const distribution = {};
  entries.forEach(({ subjectId, count }) => {
    const key = (subjectId || "").trim();
    const parsed = Number(count);
    if (!key || !Number.isFinite(parsed) || parsed < 1) return;
    distribution[key] = parsed;
  });
  return distribution;
}

export function apiErrorMessage(error) {
  if (!error) return "Something went wrong.";
  if (typeof error.message === "string" && error.message) return error.message;
  return "Request failed.";
}
