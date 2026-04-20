import type { Contradiction, ResearchClaim } from "@/types/api";

export function ClaimList({ claims }: { claims: ResearchClaim[] }) {
  if (claims.length === 0) {
    return <p className="text-sm text-muted">No claims have been saved for this run.</p>;
  }

  return (
    <ul className="space-y-3">
      {claims.map((claim) => (
        <li key={claim.id} className="rounded-2xl border border-line bg-panel px-5 py-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-line px-2 py-0.5 text-[11px] uppercase tracking-wide text-muted">
              {claim.kind}
            </span>
            {claim.verification ? (
              <span className="rounded-full border border-brass/40 px-2 py-0.5 text-[11px] uppercase tracking-wide text-brass">
                {claim.verification.status}
              </span>
            ) : (
              <span className="text-xs text-muted">Not checked yet</span>
            )}
          </div>
          <p className="mt-3 font-serif text-lg leading-snug text-foreground">{claim.text}</p>
          <p className="mt-2 break-all text-xs text-sea">{claim.source_url}</p>
          {claim.verification?.explanation ? (
            <p className="mt-3 text-sm leading-6 text-muted">{claim.verification.explanation}</p>
          ) : null}
          {claim.verification?.supporting_excerpt ? (
            <blockquote className="mt-3 border-l border-brass/50 pl-3 text-sm leading-6 text-foreground">
              {claim.verification.supporting_excerpt}
            </blockquote>
          ) : null}
          {claim.verification?.opposing_excerpt ? (
            <blockquote className="mt-3 border-l border-danger/50 pl-3 text-sm leading-6 text-foreground">
              {claim.verification.opposing_excerpt}
            </blockquote>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

export function ContradictionList({ items }: { items: Contradiction[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-muted">No cross-source disagreements have been saved.</p>;
  }

  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={`${item.source_url}-${item.other_source_url}-${item.explanation}`} className="rounded-2xl border border-line bg-panel px-5 py-4">
          <p className="text-sm leading-6 text-foreground">{item.explanation}</p>
          {item.context ? <p className="mt-2 text-sm leading-6 text-muted">{item.context}</p> : null}
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <QuotedClaim text={item.claim_text} url={item.source_url} />
            <QuotedClaim text={item.other_claim_text} url={item.other_source_url} />
          </div>
        </li>
      ))}
    </ul>
  );
}

function QuotedClaim({ text, url }: { text: string; url: string }) {
  return (
    <div className="rounded-xl bg-ink px-3 py-3">
      <p className="text-sm leading-6 text-foreground">{text}</p>
      <p className="mt-2 break-all text-xs text-sea">{url}</p>
    </div>
  );
}
