"use client";

import { PageHeader } from "@/components/PageHeader";
import { QuestionSection } from "@/features/research/QuestionSection";
import { QuestionList } from "@/features/research/QuestionList";
import { useResearchQuestions } from "@/hooks/useResearchQuestions";

export function History() {
  const { questions, loading, error, reload } = useResearchQuestions(50);

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="History"
        title="Questions saved so far."
        lede="Newest first. Open a question to read the sources, claims, checks, disagreements, and report that were actually saved."
      />
      <QuestionSection
        loading={loading}
        error={error}
        count={questions.length}
        onRetry={() => {
          void reload();
        }}
        emptyTitle="No history yet"
        emptyBody="Start a question from the desk. It will be listed here with the status returned by the API."
      >
        <QuestionList questions={questions} />
      </QuestionSection>
    </div>
  );
}
