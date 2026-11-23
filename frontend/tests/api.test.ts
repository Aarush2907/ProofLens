import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, createResearchQuestion, exportHref, fetchHealth, fetchResearchQuestions, fetchResearchSession } from "../lib/api";

const question = {
  id: "6f1c0a4e-2b4d-4e2a-9c1a-0b1d2e3f4a5b",
  question: "What evidence links sleep and memory consolidation?",
  status: "submitted",
  created_at: "2026-11-23T09:00:00+00:00",
  updated_at: "2026-11-23T09:00:00+00:00",
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("research API client", () => {
  it("builds export links from the configured API origin", () => {
    expect(exportHref(question.id, "md")).toBe(
      `http://localhost:8000/api/research/${question.id}/export.md`,
    );
    expect(exportHref(question.id, "pdf")).toBe(
      `http://localhost:8000/api/research/${question.id}/export.pdf`,
    );
  });

  it("reads a degraded health report without treating it as a crash", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 503,
        ok: false,
        json: async () => ({
          status: "degraded",
          service: "ProofLens",
          environment: "development",
          database: "unavailable",
          version: "0.1.0",
          time: "2026-11-23T09:00:00+00:00",
        }),
      }),
    );

    const report = await fetchHealth();
    expect(report.database).toBe("unavailable");
    expect(report.status).toBe("degraded");
  });

  it("turns a network failure into an API error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    await expect(fetchResearchQuestions(5)).rejects.toBeInstanceOf(ApiError);
  });

  it("posts a question and returns the saved record", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      status: 201,
      ok: true,
      json: async () => question,
    });
    vi.stubGlobal("fetch", fetchMock);

    const saved = await createResearchQuestion(question.question);

    expect(saved.status).toBe("submitted");
    expect(saved.question).toBe(question.question);
    const [, init] = fetchMock.mock.calls[0];
    expect(JSON.parse(init.body)).toEqual({ question: question.question });
  });

  it("surfaces the backend validation message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 422,
        ok: false,
        json: async () => ({
          error: { code: "validation_error", message: "Write at least 10 characters so the question is specific enough to research later." },
        }),
      }),
    );

    await expect(createResearchQuestion("short")).rejects.toThrow(/10 characters/);
  });

  it("rejects a session body that has no source list", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 200,
        ok: true,
        json: async () => question,
      }),
    );

    await expect(fetchResearchSession(question.id)).rejects.toThrow(/could not be loaded/);
  });
});
