"use client";

import { useActivityStream, type StreamConnection } from "@/hooks/useActivityStream";

const AGENT_LABELS: Record<string, string> = {
  workflow: "Workflow",
  researcher: "Researcher",
  extractor: "Extractor",
  fact_checker: "Fact-checker",
  contradiction_detector: "Contradiction detector",
  review: "Review",
  writer: "Writer",
};

export function ActivityPanel({ sessionId }: { sessionId: string }) {
  const { events, latest, connection } = useActivityStream(sessionId);
  const agent = latest ? AGENT_LABELS[latest.agent] ?? latest.agent : "Workflow";
  const failed = latest?.kind === "research_failed";

  return (
    <section id="activity" className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h2 className="font-serif text-2xl text-foreground">Agent activity</h2>
        <p className="text-xs uppercase tracking-[0.16em] text-muted">{connectionLabel(connection)}</p>
      </div>
      <div className="rounded-2xl border border-line bg-panel px-5 py-4">
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-brass">{agent}</p>
        <p className={`mt-2 text-sm ${failed ? "text-danger" : "text-foreground"}`}>
          {latest ? latest.message : "Waiting for the first event from this run."}
        </p>
      </div>
      {events.length > 0 ? (
        <ol className="space-y-2">
          {events.map((event) => (
            <li key={event.id} className="rounded-xl border border-line bg-panel/60 px-4 py-3">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="text-xs uppercase tracking-[0.14em] text-brass">
                  {AGENT_LABELS[event.agent] ?? event.agent}
                </p>
                <p className="text-xs text-muted">{event.kind.replace(/_/g, " ")}</p>
              </div>
              <p className={`mt-1 text-sm ${event.kind === "research_failed" ? "text-danger" : "text-foreground"}`}>
                {event.message}
              </p>
            </li>
          ))}
        </ol>
      ) : (
        <p className="text-sm text-muted">Events appear here as each agent finishes a real step.</p>
      )}
    </section>
  );
}

function connectionLabel(connection: StreamConnection): string {
  if (connection === "live") return "Live";
  if (connection === "reconnecting") return "Reconnecting";
  if (connection === "closed") return "Stream closed";
  return "Connecting";
}
