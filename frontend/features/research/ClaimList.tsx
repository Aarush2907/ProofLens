import type { Contradiction, ResearchClaim } from "@/types/api";


export function ClaimList({ claims }: { claims: ResearchClaim[] }) {
  if (claims.length === 0) {
    return <p className="text-sm text-muted">No claims have been saved for this run.</p>;
  }

  return (
    <ul className="space-y-3">
      {claims.map((claim) => (
        <li key={claim.id} id={`claim-${claim.id}`} className="rounded-2xl border border-line bg-panel px-5 py-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-line px-2 py-0.5 text-[11px] uppercase tracking-wide text-muted">
              {claim.kind}
            </span>
            <span className="rounded-full border border-line px-2 py-0.5 text-[11px] uppercase tracking-wide text-muted">
              {claim.review_status}
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
          <a href={claim.source_url} className="mt-2 block break-all text-xs text-sea hover:text-foreground" target="_blank" rel="noreferrer">
            {claim.source_url}
          </a>
          {claim.verification?.explanation ? (
            <p className="mt-3 text-sm leading-6 text-muted">{claim.verification.explanation}</p>
          ) : null}
          <EvidenceGroup title="Supporting evidence" stance="supporting" items={claim.evidence} />
          <EvidenceGroup title="Opposing evidence" stance="opposing" items={claim.evidence} />
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

function EvidenceGroup({
  title,
  stance,
  items,
}: {
  title: string;
  stance: string;
  items: ResearchClaim["evidence"];
}) {
  const matches = items.filter((item) => item.stance === stance);
  return (
    <div className="mt-4">
      <h3 className="text-xs font-medium uppercase tracking-[0.16em] text-brass">{title}</h3>
      {matches.length === 0 ? (
        <p className="mt-2 text-sm text-muted">No saved passage.</p>
      ) : (
        matches.map((item) => (
          <blockquote key={item.id} className="mt-2 border-l border-brass/50 pl-3 text-sm leading-6 text-foreground">
            {item.passage}
            <a href={item.source_url} className="mt-1 block break-all text-xs text-sea" target="_blank" rel="noreferrer">
              {item.source_url}
            </a>
          </blockquote>
        ))
      )}
    </div>
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
