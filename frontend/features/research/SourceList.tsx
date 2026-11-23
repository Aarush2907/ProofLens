import { formatSavedAt } from "@/lib/format";
import type { ResearchSource } from "@/types/api";

const ROLE_LABEL: Record<string, string> = {
  primary: "Primary-style source",
  secondary: "Secondary or unidentified",
  unclear: "Incomplete primary-source signals",
};

export function SourceList({ sources }: { sources: ResearchSource[] }) {
  if (sources.length === 0) {
    return <p className="text-sm text-muted">No sources have been saved for this run.</p>;
  }

  return (
    <ul className="space-y-3">
      {sources.map((source, index) => {
        const passage = source.content.trim();
        const showPassage = passage.length > 0 && passage !== source.snippet.trim();
        return (
          <li key={source.id} id={`source-${index + 1}`} className="scroll-mt-6 rounded-2xl border border-line bg-panel px-5 py-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-raised px-2 py-0.5 text-xs text-foreground">[{index + 1}]</span>
              <span className="rounded-full border border-brass/40 px-2 py-0.5 text-[11px] uppercase tracking-wide text-brass">
                {ROLE_LABEL[source.quality.role] ?? source.quality.role}
              </span>
              <span className="text-xs text-muted">{source.domain || source.quality.publisher}</span>
            </div>
            <a href={source.url} className="mt-3 block font-serif text-xl text-foreground hover:text-brass" target="_blank" rel="noreferrer">
              {source.title}
            </a>
            <p className="mt-1 break-all text-xs text-sea">{source.url}</p>
            <p className="mt-2 text-xs text-muted">
              {source.author || "Author not retrieved"}
              <span aria-hidden="true"> · </span>
              {source.published_on || "Publication date not retrieved"}
              {source.retrieved_at ? <span> · Retrieved {formatSavedAt(source.retrieved_at)}</span> : null}
            </p>
            {source.search_query ? <p className="mt-2 text-xs text-muted">Search query: {source.search_query}</p> : null}
            {source.snippet ? <p className="mt-3 text-sm leading-6 text-foreground">{source.snippet}</p> : null}
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm leading-6 text-muted">
              {source.quality.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
            {showPassage ? (
              <details className="mt-3">
                <summary className="cursor-pointer text-sm text-brass">Retrieved passage</summary>
                <p className="mt-2 text-sm leading-6 text-muted">{passage}</p>
              </details>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}
