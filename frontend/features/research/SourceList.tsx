import type { ResearchSource } from "@/types/api";

export function SourceList({ sources }: { sources: ResearchSource[] }) {
  if (sources.length === 0) {
    return <p className="text-sm text-muted">No sources have been saved for this run.</p>;
  }

  return (
    <ul className="space-y-3">
      {sources.map((source) => {
        const passage = source.content.trim();
        const showPassage = passage.length > 0 && passage !== source.snippet.trim();
        return (
          <li key={source.url} className="rounded-2xl border border-line bg-panel px-5 py-4">
            <a href={source.url} className="font-serif text-xl text-foreground hover:text-brass" target="_blank" rel="noreferrer">
              {source.title}
            </a>
            <p className="mt-1 break-all text-xs text-sea">{source.url}</p>
            {source.search_query ? (
              <p className="mt-2 text-xs text-muted">Search query: {source.search_query}</p>
            ) : null}
            {source.snippet ? <p className="mt-3 text-sm leading-6 text-foreground">{source.snippet}</p> : null}
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
