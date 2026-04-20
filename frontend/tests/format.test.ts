import { describe, expect, it } from "vitest";
import { formatSavedAt, stageDetail, statusDetail, statusLabel } from "../lib/format";

describe("research presentation", () => {
  it("labels a saved run without inventing a result", () => {
    expect(statusLabel("submitted")).toBe("Submitted");
    expect(statusDetail("submitted")).toBe("Saved. Research has not run.");
    expect(statusLabel("running")).toBe("Running");
    expect(statusDetail("completed")).toBe("A report was saved from this run.");
    expect(statusLabel("failed")).toBe("Failed");
  });

  it("does not invent a label for an unknown status", () => {
    expect(statusLabel("review")).toBe("review");
    expect(statusDetail("review")).toBe("Recorded. No findings are attached.");
  });

  it("describes a stage only when the run has reached it", () => {
    expect(stageDetail("sources_collected", "running")).toMatch(/extractor has not finished/);
    expect(stageDetail("completed", "completed")).toMatch(/report was saved/);
    expect(stageDetail("mystery", "running")).toBe("Research is in progress.");
  });
  it("returns the original text when the timestamp cannot be parsed", () => {
    expect(formatSavedAt("not-a-date")).toBe("not-a-date");
  });
});
