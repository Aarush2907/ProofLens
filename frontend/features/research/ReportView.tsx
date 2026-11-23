import { exportHref } from "@/lib/api";
import {
  TONE_CLASS,
  VERDICTS,
  certaintyLabel,
  certaintyTone,
  rejectedCount,
  sourceNumbers,
  tallyClaims,
  toneFor,
  urlKey,
} from "@/lib/report";
import type { ResearchClaim, ResearchReport, ResearchSource } from "@/types/api";

export function ReportView({
  report,
  questionId,
  claims,
  sources,
}: {
  report: ResearchReport | null;
  questionId: string;
  claims: ResearchClaim[];
  sources: ResearchSource[];
}) {
  return (
    <div className="space-y-5">
      <Downloads questionId={questionId} />
      {report === null ? (
        <p className="rounded-2xl border border-line bg-panel px-5 py-4 text-sm leading-6 text-muted">
          No report has been written for this run yet. The downloads still include the question and all the
          evidence saved so far.
        </p>
      ) : (
        <ReportBody report={report} claims={claims} sources={sources} />
      )}
    </div>
  );
}

function Downloads({ questionId }: { questionId: string }) {
  const style =
    "inline-flex items-center rounded-full border border-brass/50 px-4 py-1.5 text-sm text-brass transition-colors hover:bg-brass hover:text-ink";
  return (
    <div className="flex flex-wrap items-center gap-3">
      <a className={style} href={exportHref(questionId, "pdf")}>
        Download PDF
      </a>
      <a className={style} href={exportHref(questionId, "md")}>
        Download Markdown
      </a>
      <span className="text-xs text-muted">Both include the sources, quotations and review decisions.</span>
    </div>
  );
}

function ReportBody({
  report,
  claims,
  sources,
}: {
  report: ResearchReport;
  claims: ResearchClaim[];
  sources: ResearchSource[];
}) {
  const numbers = sourceNumbers(sources);
  const rejected = rejectedCount(claims);

  return (
    <article className="space-y-8 rounded-2xl border border-line bg-panel px-5 py-6 sm:px-7">
      <section>
        <h3 className="text-xs font-medium uppercase tracking-[0.16em] text-brass">Summary</h3>
        <p className="mt-3 font-serif text-xl leading-8 text-foreground">{report.summary}</p>
      </section>

      <section>
        <h3 className="text-xs font-medium uppercase tracking-[0.16em] text-brass">Verdicts at a glance</h3>
        <ul className="mt-3 grid grid-cols-2 gap-3 lg:grid-cols-4">
          {tallyClaims(claims).map((item) => (
            <li key={item.status} className={`rounded-xl border px-4 py-3 ${TONE_CLASS[toneFor(item.status)]}`}>
              <p className="text-2xl font-medium">{item.count}</p>
              <p className="mt-1 text-xs uppercase tracking-wide">{item.status}</p>
            </li>
          ))}
        </ul>
        {rejected > 0 ? (
          <p className="mt-2 text-xs text-muted">
            {rejected} more claim{rejected === 1 ? " was" : "s were"} rejected in review and left out of the counts.
          </p>
        ) : null}
      </section>

      <section>
        <h3 className="text-xs font-medium uppercase tracking-[0.16em] text-brass">Key findings</h3>
        {report.findings.length === 0 ? (
          <p className="mt-3 text-sm text-muted">No finding with a saved citation was available.</p>
        ) : (
          <ol className="mt-3 space-y-5">
            {report.findings.map((finding, index) => (
              <li key={finding.text} className="flex gap-4">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-line text-xs text-muted">
                  {index + 1}
                </span>
                <div>
                  <p className="text-[15px] leading-7 text-foreground">{finding.text}</p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <span
                      className={`rounded-full border px-2 py-0.5 text-[11px] uppercase tracking-wide ${TONE_CLASS[certaintyTone(finding.certainty)]}`}
                    >
                      {certaintyLabel(finding.certainty)}
                    </span>
                    {finding.citation_urls.map((url) => {
                      const number = numbers.get(urlKey(url));
                      if (!number) {
                        return null;
                      }
                      const source = sources[number - 1];
                      return (
                        <a
                          key={url}
                          href={`#source-${number}`}
                          title={source.title}
                          className="rounded-full border border-line px-2 py-0.5 text-xs text-sea hover:text-foreground"
                        >
                          [{number}] {shorten(source.title || source.domain, 38)}
                        </a>
                      );
                    })}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>

      <ReportNotes title="What remains uncertain" items={report.uncertainties} />
      <ReportNotes title="Limitations" items={report.limitations} />

      <details className="rounded-xl border border-line px-4 py-3 text-sm text-muted">
        <summary className="cursor-pointer text-foreground">How to read the verdicts</summary>
        <ul className="mt-3 space-y-2 leading-6">
          {VERDICTS.map((verdict) => (
            <li key={verdict.status}>
              <span className={`mr-2 rounded-full border px-2 py-0.5 text-[11px] uppercase tracking-wide ${TONE_CLASS[verdict.tone]}`}>
                {verdict.status}
              </span>
              {verdict.meaning}
            </li>
          ))}
        </ul>
        <p className="mt-3 leading-6">
          A verdict describes the collected passages only. A page can be wrong, so Verified is not a guarantee
          that a claim is true.
        </p>
      </details>
    </article>
  );
}

function ReportNotes({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) {
    return null;
  }
  return (
    <section>
      <h3 className="text-xs font-medium uppercase tracking-[0.16em] text-brass">{title}</h3>
      <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-muted">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function shorten(text: string, length: number): string {
  return text.length > length ? `${text.slice(0, length - 1)}…` : text;
}
