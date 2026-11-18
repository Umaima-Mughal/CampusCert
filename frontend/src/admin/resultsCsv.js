/**
 * src/admin/resultsCsv.js
 *
 * Frontend-only CSV helpers for the Admin "Student results" page.
 * No network calls, no backend changes.
 */

const HEADERS = [
  "Student Name",
  "Student Email",
  "Paper Name",
  "Examination Result",
];

/** Quote a cell if it contains a comma, quote, or line break. */
function escapeCsvCell(value) {
  if (value === null || value === undefined) return "";
  const text = String(value);
  if (/[",\r\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

/**
 * Build CSV text from the rows currently shown on the page.
 * `rows` items: { studentName, studentEmail, paperName, resultText }
 * where resultText is "" for ungraded attempts (never invented).
 */
export function buildResultsCsv(rows) {
  const lines = [HEADERS.map(escapeCsvCell).join(",")];
  for (const row of rows) {
    lines.push(
      [row.studentName, row.studentEmail, row.paperName, row.resultText]
        .map(escapeCsvCell)
        .join(",")
    );
  }
  return lines.join("\r\n");
}

/** Trigger a browser download of CSV text. BOM keeps non-ASCII names correct in Excel. */
export function downloadCsv(filename, csvText) {
  const blob = new Blob(["\uFEFF" + csvText], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}