"use client";

import type { ReactNode } from "react";
import Link from "next/link";
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
        {session.error_message && session.stage !== "awaiting_review" ? (
          <p className="mt-4 text-sm text-danger" role="alert">
            {session.error_message}
          </p>
        ) : null}
        <nav className="mt-6 flex flex-wrap gap-4 text-sm text-brass">
          {session.stage === "awaiting_review" ? <a href="#review">Review</a> : null}
          <a href="#evidence-graph">Evidence graph</a>
          <a href="#sources">Sources</a>
          <a href="#claims">Claims</a>
          <a href="#report">Report</a>
        </nav>
      </div>

      <ReviewPanel session={session} onSubmitted={reload} />
      <Section title="Evidence graph" id="evidence-graph">
        <EvidenceGraphView sessionId={session.id} refreshKey={`${session.stage}:${session.updated_at}`} />
      </Section>
      <Section title="Sources" id="sources">
        <SourceList sources={session.sources} />
      </Section>
      <Section title="Claims and verification" id="claims">
        <ClaimList claims={session.claims} />
      </Section>
      <Section title="Contradictions">
        <ContradictionList items={session.contradictions} />
      </Section>
      <Section title="Report" id="report">
        <ReportView report={session.report} />
      </Section>
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
