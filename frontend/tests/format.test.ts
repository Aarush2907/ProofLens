import { describe, expect, it } from "vitest";
import { formatSavedAt, statusDetail, statusLabel } from "../lib/format";

describe("research presentation", () => {
  it("labels a submitted question without implying a finished report", () => {
    expect(statusLabel("submitted")).toBe("Submitted");
    expect(statusDetail("submitted")).toBe("Saved. Research has not run.");
  });

  it("does not invent a label for an unknown status", () => {
    expect(statusLabel("review")).toBe("review");
    expect(statusDetail("review")).toBe("Recorded. No findings are attached.");
  });

  it("returns the original text when the timestamp cannot be parsed", () => {
    expect(formatSavedAt("not-a-date")).toBe("not-a-date");
  });
});
