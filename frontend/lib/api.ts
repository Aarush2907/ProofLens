import type {
  HealthReport,
  ResearchQuestion,
  ResearchSession,
  ResearchSource,
} from "@/types/api";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function apiUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }
  return "http://localhost:8000";
}

function messageFrom(body: unknown, fallback: string): string {
  if (typeof body !== "object" || body === null || !("error" in body)) {
    return fallback;
  }
  const message = (body as { error?: { message?: unknown } }).error?.message;
  if (typeof message === "string" && message.trim()) {
    return message;
  }
  return fallback;
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(`${apiUrl()}${path}`, {
      ...init,
      cache: "no-store",
      headers: {
        Accept: "application/json",
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError(
      "The ProofLens API is not reachable. Start the backend and try again.",
      0,
    );
  }
}

function isHealthReport(value: unknown): value is HealthReport {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const status = (value as { status?: unknown }).status;
  return status === "ok" || status === "degraded";
}

function isResearchQuestion(value: unknown): value is ResearchQuestion {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    typeof record.id === "string" &&
    typeof record.question === "string" &&
    typeof record.status === "string" &&
    typeof record.created_at === "string"
  );
}

export async function fetchHealth(): Promise<HealthReport> {
  const response = await request("/api/health");
  const body = await readJson(response);
  if ((response.status === 200 || response.status === 503) && isHealthReport(body)) {
    return body;
  }
  throw new ApiError(messageFrom(body, "The health check failed."), response.status);
}

export async function fetchResearchQuestions(limit: number): Promise<ResearchQuestion[]> {
  const response = await request(`/api/research?limit=${limit}`);
  const body = await readJson(response);
  if (!response.ok) {
    throw new ApiError(messageFrom(body, "Saved questions could not be loaded."), response.status);
  }
  if (!Array.isArray(body) || !body.every(isResearchQuestion)) {
    throw new ApiError("The research list response was not usable.", response.status);
  }
  return body;
}

function isResearchSource(value: unknown): value is ResearchSource {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return typeof record.url === "string" && typeof record.title === "string";
}

function isResearchSession(value: unknown): value is ResearchSession {
  if (!isResearchQuestion(value)) {
    return false;
  }
  const record = value as unknown as Record<string, unknown>;
  return (
    Array.isArray(record.sources) &&
    record.sources.every(isResearchSource) &&
    Array.isArray(record.claims) &&
    Array.isArray(record.contradictions)
  );
}

export async function fetchResearchSession(id: string): Promise<ResearchSession> {
  const response = await request(`/api/research/${id}`);
  const body = await readJson(response);
  if (!response.ok || !isResearchSession(body)) {
    throw new ApiError(messageFrom(body, "That research run could not be loaded."), response.status);
  }
  return body;
}

export async function createResearchQuestion(question: string): Promise<ResearchQuestion> {
  const response = await request("/api/research", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  const body = await readJson(response);
  if (!response.ok || !isResearchQuestion(body)) {
    throw new ApiError(messageFrom(body, "The question could not be saved."), response.status);
  }
  return body;
}
