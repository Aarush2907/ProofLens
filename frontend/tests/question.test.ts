import { describe, expect, it } from "vitest";
import { validateQuestion } from "../lib/question";

describe("validateQuestion", () => {
  it("accepts a specific question and trims it only for the length check", () => {
    expect(validateQuestion("  What evidence links sleep and memory?  ")).toBeNull();
  });

  it("rejects a short question", () => {
    expect(validateQuestion("   too short  ")).toMatch(/10 characters/);
  });

  it("rejects a question over 2000 characters", () => {
    expect(validateQuestion("a".repeat(2001))).toMatch(/2000/);
  });
});
