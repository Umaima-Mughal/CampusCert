import { describe, it, expect } from "vitest";
import { entriesToDistribution, statusLabel, toIsoOrNull } from "../admin/examUtils";

describe("examUtils", () => {
  it("maps exam status labels", () => {
    expect(statusLabel("DRAFT")).toBe("Draft");
    expect(statusLabel("ACTIVE")).toBe("Active");
  });

  it("builds distribution maps from form rows", () => {
    expect(
      entriesToDistribution([
        { subjectId: " math ", count: "5" },
        { subjectId: "", count: "2" },
        { subjectId: "skip", count: "0" },
      ])
    ).toEqual({ math: 5 });
  });

  it("converts datetime-local values to ISO or null", () => {
    expect(toIsoOrNull("")).toBeNull();
    expect(typeof toIsoOrNull("2026-09-24T09:00")).toBe("string");
  });
});
