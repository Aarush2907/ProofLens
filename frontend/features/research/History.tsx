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
        lede="Newest first. Each question stays submitted until a later milestone can research it. There is no score, citation, or agent activity on this page."
      />
      <QuestionSection
        loading={loading}
        error={error}
        count={questions.length}
        onRetry={() => {
          void reload();
        }}
        emptyTitle="No history yet"
        emptyBody="Save a question from the desk. It will be listed here as submitted, and only as submitted."
      >
        <QuestionList questions={questions} />
      </QuestionSection>
    </div>
  );
}
