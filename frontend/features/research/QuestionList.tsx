import Link from "next/link";
import { formatSavedAt, statusDetail, statusLabel } from "@/lib/format";
import type { ResearchQuestion } from "@/types/api";

export function QuestionList({ questions }: { questions: ResearchQuestion[] }) {
  return (
    <ul className="space-y-3">
      {questions.map((item) => (
        <li key={item.id}>
          <Link
            href={`/research/${item.id}`}
            className="block rounded-2xl border border-line bg-panel px-5 py-4 transition-colors hover:border-brass/40"
          >
            <div className="flex items-start justify-between gap-4">
              <h3 className="font-serif text-xl leading-snug text-foreground">{item.question}</h3>
              <span className="shrink-0 rounded-full border border-brass/40 px-2.5 py-1 text-[11px] uppercase tracking-wide text-brass">
                {statusLabel(item.status)}
              </span>
            </div>
            <p className="mt-3 text-sm text-muted">
              {formatSavedAt(item.created_at)}
              <span aria-hidden="true"> · </span>
              {item.error_message || statusDetail(item.status)}
            </p>
          </Link>
        </li>
      ))}
    </ul>
  );
}
