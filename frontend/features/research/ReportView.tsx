import type { ResearchReport } from "@/types/api";

export function ReportView({ report }: { report: ResearchReport | null }) {
  if (report === null) {
    return <p className="text-sm text-muted">No report has been saved for this run.</p>;
  }

  return (
    <article className="space-y-6 rounded-2xl border border-line bg-panel px-5 py-5 sm:px-6">
      <p className="font-serif text-xl leading-8 text-foreground">{report.summary}</p>
      {report.findings.length > 0 ? (
        <section>
          <h3 className="text-sm font-medium uppercase tracking-[0.16em] text-brass">Findings</h3>
          <ul className="mt-3 space-y-4">
            {report.findings.map((finding) => (
              <li key={finding.text}>
                <p className="text-sm leading-6 text-foreground">{finding.text}</p>
                <p className="mt-1 text-xs uppercase tracking-wide text-muted">{finding.certainty}</p>
                <ul className="mt-2 space-y-1">
                  {finding.citation_urls.map((url) => (
                    <li key={url}>
                      <a href={url} className="break-all text-xs text-sea hover:text-foreground" target="_blank" rel="noreferrer">
                        {url}
                      </a>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      <ReportNotes title="Uncertainty" items={report.uncertainties} />
      <ReportNotes title="Limitations" items={report.limitations} />
    </article>
  );
}

function ReportNotes({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) {
    return null;
  }
  return (
    <section>
      <h3 className="text-sm font-medium uppercase tracking-[0.16em] text-brass">{title}</h3>
      <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-muted">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
