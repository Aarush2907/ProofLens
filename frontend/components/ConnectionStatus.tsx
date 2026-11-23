"use client";

import { useHealth } from "@/hooks/useHealth";

export function ConnectionStatus() {
  const { report, unreachable } = useHealth();

  let label = "Checking the API…";
  let tone = "bg-muted";

  if (unreachable) {
    label = "API unavailable";
    tone = "bg-danger";
  } else if (report?.database === "connected" && report.qdrant === "unavailable") {
    label = "API online · Database connected · Qdrant unavailable";
    tone = "bg-brass";
  } else if (report?.database === "connected") {
    label = "API online · Database connected";
    tone = "bg-ok";
  } else if (report) {
    label = "API online · Database unavailable";
    tone = "bg-brass";
  }

  return (
    <p className="flex items-center gap-2 text-xs text-muted" role="status">
      <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${tone}`} aria-hidden="true" />
      {label}
    </p>
  );
}
