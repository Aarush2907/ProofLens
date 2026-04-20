"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/PageHeader";
import { QuestionForm } from "@/features/research/QuestionForm";
import { QuestionList } from "@/features/research/QuestionList";
import { QuestionSection } from "@/features/research/QuestionSection";
import { useResearchQuestions } from "@/hooks/useResearchQuestions";
import { createResearchQuestion } from "@/lib/api";

export function Desk() {
  const router = useRouter();
  const { questions, loading, error, reload } = useResearchQuestions(5);

  return (
    <div className="space-y-10">
      <PageHeader
        eyebrow="Research desk"
        title="Ask a question worth checking."
        lede="ProofLens searches for sources, extracts claims, checks them against the retrieved passages, looks for disagreements, and writes a cited report. The page for a run shows only what those steps have saved."
      />
      <QuestionForm
        onSubmit={async (question) => {
          const saved = await createResearchQuestion(question);
          await reload();
          router.push(`/research/${saved.id}`);
        }}
      />
      <section className="space-y-4">
        <div className="flex items-end justify-between gap-4">
          <h2 className="font-serif text-2xl text-foreground">Recent questions</h2>
          {questions.length > 0 ? (
            <Link href="/history" className="text-sm text-brass hover:text-foreground">
              View history
            </Link>
          ) : null}
        </div>
        <QuestionSection
          loading={loading}
          error={error}
          count={questions.length}
          onRetry={() => {
            void reload();
          }}
          emptyTitle="Nothing on the desk yet"
          emptyBody="A question you start will appear here with its real status. Open it to read the sources, claims, and report after they are saved."
        >
          <QuestionList questions={questions} />
        </QuestionSection>
      </section>
    </div>
  );
}
