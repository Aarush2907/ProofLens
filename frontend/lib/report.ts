import type { ResearchClaim, ResearchSource } from "../types/api";

export type Tone = "ok" | "partial" | "bad" | "unknown";

export const VERDICTS: { status: string; meaning: string; tone: Tone }[] = [
  { status: "Verified", meaning: "A saved passage states this claim directly.", tone: "ok" },
  { status: "Partially supported", meaning: "A saved passage supports only part of the claim.", tone: "partial" },
  { status: "Contradicted", meaning: "A saved passage conflicts with the claim.", tone: "bad" },
  { status: "Insufficient evidence", meaning: "The collected passages do not settle this claim.", tone: "unknown" },
];

export const TONE_CLASS: Record<Tone, string> = {
  ok: "border-ok/50 bg-ok/10 text-ok",
  partial: "border-brass/50 bg-brass/10 text-brass",
  bad: "border-danger/50 bg-danger/10 text-danger",
  unknown: "border-line bg-raised text-muted",
};

export function toneFor(status: string): Tone {
  return VERDICTS.find((verdict) => verdict.status === status)?.tone ?? "unknown";
}

export function meaningFor(status: string): string {
  return VERDICTS.find((verdict) => verdict.status === status)?.meaning ?? "";
}

export function statusOf(claim: ResearchClaim): string {
  return claim.verification?.status ?? "Insufficient evidence";
}

// Rejected claims are shown apart. The report does not rely on them.
export function tallyClaims(claims: ResearchClaim[]): { status: string; count: number }[] {
  const kept = claims.filter((claim) => claim.review_status !== "rejected");
  return VERDICTS.map(({ status }) => ({
    status,
    count: kept.filter((claim) => statusOf(claim) === status).length,
  }));
}

export function rejectedCount(claims: ResearchClaim[]): number {
  return claims.filter((claim) => claim.review_status === "rejected").length;
}

export function urlKey(url: string): string {
  return url.trim().replace(/#.*$/, "").replace(/\/$/, "").toLowerCase();
}

// Sources are numbered in the order they were saved. Findings and claims cite these numbers.
export function sourceNumbers(sources: ResearchSource[]): Map<string, number> {
  const numbers = new Map<string, number>();
  sources.forEach((source, index) => numbers.set(urlKey(source.url), index + 1));
  return numbers;
}

export function certaintyLabel(certainty: string): string {
  if (certainty === "supported") return "Supported by a verified claim";
  if (certainty === "partial") return "Partly supported";
  return "Uncertain";
}

export function certaintyTone(certainty: string): Tone {
  if (certainty === "supported") return "ok";
  if (certainty === "partial") return "partial";
  return "unknown";
}
