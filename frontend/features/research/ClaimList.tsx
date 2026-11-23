import { TONE_CLASS, VERDICTS, meaningFor, sourceNumbers, statusOf, toneFor, urlKey } from "@/lib/report";
import type { Contradiction, ResearchClaim, ResearchSource } from "@/types/api";

export function ClaimList({ claims, sources }: { claims: ResearchClaim[]; sources: ResearchSource[] }) {
  if (claims.length === 0) {
    return <p className="text-sm text-muted">No claims have been saved for this run.</p>;
  }

  const numbers = sourceNumbers(sources);
  const kept = claims.filter((claim) => claim.review_status !== "rejected");
  const rejected = claims.filter((claim) => claim.review_status === "rejected");

  return (
    <div className="space-y-8">
      {VERDICTS.map((verdict) => {
        const group = kept.filter((claim) => statusOf(claim) === verdict.status);
        if (group.length === 0) {
          return null;
        }
        return (
          <div key={verdict.status}>
            <div className="flex flex-wrap items-baseline gap-3">
              <h3 className="text-sm font-medium text-foreground">
                {verdict.status} <span className="text-muted">({group.length})</span>
              </h3>
              <p className="text-xs text-muted">{verdict.meaning}</p>
            </div>
            <ul className="mt-3 space-y-3">
              {group.map((claim) => (
                <ClaimCard key={claim.id} claim={claim} sources={sources} numbers={numbers} />
              ))}
            </ul>
          </div>
        );
      })}
      {rejected.length > 0 ? (
        <div>
          <h3 className="text-sm font-medium text-foreground">
            Rejected in review <span className="text-muted">({rejected.length})</span>
          </h3>
          <p className="mt-1 text-xs text-muted">A person removed these claims, so the report does not rely on them.</p>
          <ul className="mt-3 space-y-2">
            {rejected.map((claim) => (
              <li key={claim.id} className="rounded-xl border border-line px-4 py-3 text-sm leading-6 text-muted line-through decoration-muted/50">
                {claim.text}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function ClaimCard({
  claim,
  sources,
  numbers,
}: {
  claim: ResearchClaim;
  sources: ResearchSource[];
  numbers: Map<string, number>;
}) {
  const status = statusOf(claim);
  const number = numbers.get(urlKey(claim.source_url));
  const source = number ? sources[number - 1] : undefined;
  const verification = claim.verification;

  return (
    <li id={`claim-${claim.id}`} className="rounded-2xl border border-line bg-panel px-5 py-4">
      <div className="flex flex-wrap items-center gap-2">
        {verification ? (
          <span
            title={meaningFor(status)}
            className={`rounded-full border px-2.5 py-0.5 text-[11px] uppercase tracking-wide ${TONE_CLASS[toneFor(status)]}`}
          >
            {status}
          </span>
        ) : (
          <span className="text-xs text-muted">Not checked yet</span>
        )}
        <span className="rounded-full border border-line px-2 py-0.5 text-[11px] uppercase tracking-wide text-muted">
          {claim.kind}
        </span>
        <span className="rounded-full border border-line px-2 py-0.5 text-[11px] uppercase tracking-wide text-muted">
          {claim.review_status === "approved" ? "Approved" : claim.review_status === "pending" ? "Not reviewed" : claim.review_status}
        </span>
      </div>
      <p className="mt-3 font-serif text-lg leading-snug text-foreground">{claim.text}</p>
      <p className="mt-2 text-xs text-muted">
        From{" "}
        {number && source ? (
          <a href={`#source-${number}`} className="text-sea hover:text-foreground">
            [{number}] {source.title || source.domain}
          </a>
        ) : (
          <a href={claim.source_url} className="break-all text-sea hover:text-foreground" target="_blank" rel="noreferrer">
            {claim.source_url}
          </a>
        )}
      </p>
      {verification?.explanation ? (
        <p className="mt-3 text-sm leading-6 text-muted">
          <span className="text-foreground">Why: </span>
          {verification.explanation}
        </p>
      ) : null}
      <Quote title="Supporting quotation" text={verification?.supporting_excerpt} tone="ok" />
      <Quote title="Conflicting quotation" text={verification?.opposing_excerpt} tone="bad" />
      {claim.evidence.length > 0 ? (
        <details className="mt-3">
          <summary className="cursor-pointer text-sm text-brass">
            Retrieved passages ({claim.evidence.length})
          </summary>
          <ul className="mt-2 space-y-2">
            {claim.evidence.map((item) => (
              <li key={item.id} className="text-sm leading-6 text-muted">
                <span className="mr-2 text-[11px] uppercase tracking-wide text-brass">{item.stance}</span>
                {item.passage}
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </li>
  );
}

function Quote({ title, text, tone }: { title: string; text?: string; tone: "ok" | "bad" }) {
  if (!text) {
    return null;
  }
  return (
    <blockquote className={`mt-3 border-l-2 pl-3 ${tone === "ok" ? "border-ok/60" : "border-danger/60"}`}>
      <p className="text-[11px] uppercase tracking-[0.14em] text-muted">{title}</p>
      <p className="mt-1 text-sm leading-6 text-foreground">{text}</p>
    </blockquote>
  );
}

export function ContradictionList({ items }: { items: Contradiction[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-muted">No disagreement between sources was saved.</p>;
  }

  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={`${item.source_url}-${item.other_source_url}-${item.explanation}`} className="rounded-2xl border border-danger/30 bg-panel px-5 py-4">
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
      <a href={url} className="mt-2 block break-all text-xs text-sea hover:text-foreground" target="_blank" rel="noreferrer">
        {url}
      </a>
    </div>
  );
}
