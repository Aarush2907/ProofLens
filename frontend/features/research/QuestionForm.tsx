"use client";

import { useState } from "react";
import { MAX_QUESTION_LENGTH, validateQuestion } from "@/lib/question";

export function QuestionForm({
  onSubmit,
}: {
  onSubmit: (question: string) => Promise<void>;
}) {
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const trimmedLength = draft.trim().length;
  const liveProblem = trimmedLength === 0 ? null : validateQuestion(draft);

  async function submit() {
    const problem = validateQuestion(draft);
    if (problem) {
      setNotice(null);
      setError(problem);
      return;
    }

    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      await onSubmit(draft.trim());
      setDraft("");
      setNotice("Question saved. Research has not started.");
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "The question could not be saved.";
      setError(message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form
      className="rounded-2xl border border-line bg-panel px-5 py-5 shadow-[inset_3px_0_0_0_rgba(215,176,122,0.9)] sm:px-6"
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
    >
      <label htmlFor="research-question" className="text-sm font-medium text-foreground">
        Research question
      </label>
      <textarea
        id="research-question"
        value={draft}
        onChange={(event) => {
          setDraft(event.target.value);
          setError(null);
          setNotice(null);
        }}
        onKeyDown={(event) => {
          if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
            event.preventDefault();
            void submit();
          }
        }}
        rows={5}
        maxLength={MAX_QUESTION_LENGTH + 400}
        placeholder="What evidence has changed around this claim, and which sources disagree?"
        className="mt-3 w-full resize-y rounded-xl border border-line bg-ink px-4 py-3 text-[15px] leading-7 text-foreground outline-none placeholder:text-muted/70 focus:border-brass/70"
      />
      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs text-muted">
          {trimmedLength} / {MAX_QUESTION_LENGTH}
          <span className="hidden sm:inline"> · Ctrl+Enter to save</span>
        </p>
        <button
          type="submit"
          disabled={saving || liveProblem !== null || trimmedLength === 0}
          className="inline-flex items-center justify-center rounded-full bg-brass px-5 py-2.5 text-sm font-medium text-ink transition-opacity disabled:cursor-not-allowed disabled:opacity-40"
        >
          {saving ? "Saving…" : "Start research"}
        </button>
      </div>
      <p className="mt-4 text-sm leading-6 text-muted">
        Starting research saves the question with the status “Submitted”. Sources, claims, and a
        report are not produced in this milestone.
      </p>
      {error ? (
        <p className="mt-3 text-sm text-danger" role="alert">
          {error}
        </p>
      ) : null}
      {liveProblem && !error ? <p className="mt-3 text-sm text-brass">{liveProblem}</p> : null}
      {notice ? (
        <p className="mt-3 text-sm text-sea" role="status">
          {notice}
        </p>
      ) : null}
    </form>
  );
}
