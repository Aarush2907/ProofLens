"use client";

import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { QuestionForm } from "@/features/research/QuestionForm";
import { QuestionList } from "@/features/research/QuestionList";
import { QuestionSection } from "@/features/research/QuestionSection";
import { useResearchQuestions } from "@/hooks/useResearchQuestions";
import { createResearchQuestion } from "@/lib/api";

export function Desk() {
  const { questions, loading, error, reload } = useResearchQuestions(5);

  return (
    <div className="space-y-10">
      <PageHeader
        eyebrow="Research desk"
        title="Ask a question worth checking."
        lede="Write the question you want checked. ProofLens saves it here. The research agents are not running in this milestone, so this desk will not invent sources, claims, or a report."
      />
      <QuestionForm
        onSubmit={async (question) => {
          await createResearchQuestion(question);
          await reload();
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
          emptyBody="A saved question will appear here with the time it was saved and a submitted status. It will not grow a report until research can actually run."
        >
          <QuestionList questions={questions} />
        </QuestionSection>
      </section>
    </div>
  );
}
