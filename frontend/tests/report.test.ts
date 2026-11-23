import { describe, expect, it } from "vitest";
import type { ResearchClaim, ResearchSource } from "../types/api";
import { certaintyLabel, rejectedCount, sourceNumbers, tallyClaims, urlKey } from "../lib/report";

function claim(status: string | null, review = "approved"): ResearchClaim {
  return {
    id: Math.random().toString(),
    source_id: null,
    source_url: "https://example.edu/a",
    text: "A claim long enough to read.",
    kind: "fact",
    review_status: review,
    verification: status ? { status, explanation: "", supporting_excerpt: "", opposing_excerpt: "" } : null,
    evidence: [],
  };
}

describe("report helpers", () => {
  it("counts verdicts without the claims a person rejected", () => {
    const claims = [claim("Verified"), claim("Verified", "rejected"), claim("Contradicted"), claim(null)];

    const counts = Object.fromEntries(tallyClaims(claims).map((item) => [item.status, item.count]));

    expect(counts).toEqual({
      Verified: 1,
      "Partially supported": 0,
      Contradicted: 1,
      "Insufficient evidence": 1,
    });
    expect(rejectedCount(claims)).toBe(1);
  });

  it("numbers sources in saved order and matches a citation that differs by a trailing slash", () => {
    const sources = [{ url: "https://example.edu/a/" }, { url: "https://example.org/b" }] as ResearchSource[];

    const numbers = sourceNumbers(sources);

    expect(numbers.get(urlKey("https://example.edu/a"))).toBe(1);
    expect(numbers.get(urlKey("https://example.org/b#top"))).toBe(2);
  });

  it("describes finding confidence in plain words", () => {
    expect(certaintyLabel("supported")).toBe("Supported by a verified claim");
    expect(certaintyLabel("anything else")).toBe("Uncertain");
  });
});
