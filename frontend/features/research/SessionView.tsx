"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { ActivityPanel } from "@/features/research/ActivityPanel";
import { ClaimList, ContradictionList } from "@/features/research/ClaimList";
import { EvidenceGraphView } from "@/features/research/EvidenceGraph";
import { ReportView } from "@/features/research/ReportView";
import { ReviewPanel } from "@/features/research/ReviewPanel";
import { SourceList } from "@/features/research/SourceList";
import { useResearchSession } from "@/hooks/useResearchSession";
import { formatSavedAt, stageDetail, statusLabel } from "@/lib/format";

export function SessionView({ id }: { id: string }) {
  const { session, loading, error, reload } = useResearchSession(id);

  if (loading && session === null) {
    return <p className="text-sm text-muted">Loading this research run…</p>;
  }
  if (error && session === null) {
    return (
      <div className="rounded-2xl border border-danger/40 bg-panel px-5 py-4" role="alert">
        <p className="text-sm text-danger">{error}</p>
        <button type="button" onClick={reload} className="mt-3 text-sm text-brass">
          Try again
        </button>
      </div>
    );
  }
  if (session === null) {
    return null;
  }

  const finished = session.report !== null;
  const reportView = (
    <ReportView report={session.report} questionId={session.id} claims={session.claims} sources={session.sources} />
  );
  const sections = [
    ...(finished ? [{ id: "report", label: "Report" }] : [{ id: "activity", label: "Activity" }]),
    ...(session.stage === "awaiting_review" ? [{ id: "review", label: "Review" }] : []),
    { id: "claims", label: `Claims (${session.claims.length})` },
    { id: "contradictions", label: "Disagreements" },
    { id: "sources", label: `Sources (${session.sources.length})` },
    { id: "evidence-graph", label: "Evidence graph" },
    ...(finished ? [{ id: "activity-log", label: "Activity" }] : [{ id: "report", label: "Report" }]),
  ];

  return (
    <div className="space-y-10">
      <div>
        <Link href="/history" className="text-sm text-brass hover:text-foreground">
          Back to history
        </Link>
        <p className="mt-4 text-xs font-medium uppercase tracking-[0.18em] text-brass">Research run</p>
        <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
          <h1 className="max-w-3xl font-serif text-4xl tracking-tight text-foreground">{session.question}</h1>
          <span className="rounded-full border border-brass/40 px-3 py-1 text-[11px] uppercase tracking-wide text-brass">
            {statusLabel(session.status)}
          </span>
        </div>
        <p className="mt-4 text-sm text-muted">
          {formatSavedAt(session.created_at)}
          <span aria-hidden="true"> · </span>
          {stageDetail(session.stage ?? "", session.status)}
        </p>
        {session.status === "running" ? (
          <p className="mt-2 text-sm text-muted">This page reloads when the next saved step arrives.</p>
        ) : null}
        {session.estimated_cost_usd && session.estimated_cost_usd > 0 ? (
          <p className="mt-2 text-sm text-muted">
            Approximate model cost for this run: ${session.estimated_cost_usd.toFixed(4)}. This is an estimate, not a bill.
          </p>
        ) : null}
        {session.error_message && session.stage !== "awaiting_review" ? (
          <p className="mt-4 text-sm text-danger" role="alert">
            {session.error_message}
          </p>
        ) : null}
        <nav className="mt-6 flex flex-wrap gap-2 text-sm">
          {sections.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              className="rounded-full border border-line px-3 py-1 text-muted transition-colors hover:border-brass/50 hover:text-brass"
            >
              {item.label}
            </a>
          ))}
        </nav>
      </div>

      {finished ? (
        <>
          <Section title="Report" id="report">
            {reportView}
          </Section>
          <Section title="Claims and verification" id="claims">
            <ClaimList claims={session.claims} sources={session.sources} />
          </Section>
          <Section title="Where sources disagree" id="contradictions">
            <ContradictionList items={session.contradictions} />
          </Section>
          <Section title="Sources" id="sources">
            <SourceList sources={session.sources} />
          </Section>
          <Section title="Evidence graph" id="evidence-graph">
            <EvidenceGraphView sessionId={session.id} refreshKey={`${session.stage}:${session.updated_at}`} />
          </Section>
          <details id="activity-log" className="rounded-2xl border border-line px-5 py-4">
            <summary className="cursor-pointer font-serif text-xl text-foreground">Agent activity log</summary>
            <div className="mt-4">
              <ActivityPanel sessionId={session.id} />
            </div>
          </details>
        </>
      ) : (
        <>
          <ActivityPanel sessionId={session.id} />
          <ReviewPanel session={session} onSubmitted={reload} />
          <Section title="Claims and verification" id="claims">
            <ClaimList claims={session.claims} sources={session.sources} />
          </Section>
          <Section title="Where sources disagree" id="contradictions">
            <ContradictionList items={session.contradictions} />
          </Section>
          <Section title="Sources" id="sources">
            <SourceList sources={session.sources} />
          </Section>
          <Section title="Evidence graph" id="evidence-graph">
            <EvidenceGraphView sessionId={session.id} refreshKey={`${session.stage}:${session.updated_at}`} />
          </Section>
          <Section title="Report" id="report">
            {reportView}
          </Section>
        </>
      )}
    </div>
  );
}
function Section({ title, id, children }: { title: string; id?: string; children: ReactNode }) {
  return (
    <section id={id} className="space-y-4">
      <h2 className="font-serif text-2xl text-foreground">{title}</h2>
      {children}
    </section>
  );
}
