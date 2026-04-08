"use client";

import { EmptyDesk } from "@/features/research/EmptyDesk";

export function QuestionSection({
  loading,
  error,
  count,
  onRetry,
  emptyTitle,
  emptyBody,
  children,
}: {
  loading: boolean;
  error: string | null;
  count: number;
  onRetry: () => void;
  emptyTitle: string;
  emptyBody: string;
  children: React.ReactNode;
}) {
  if (loading) {
    return <p className="text-sm text-muted">Loading saved questions…</p>;
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-danger/40 bg-panel px-5 py-4" role="alert">
        <p className="text-sm text-danger">{error}</p>
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 text-sm text-brass underline-offset-4 hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }

  if (count === 0) {
    return <EmptyDesk title={emptyTitle} body={emptyBody} />;
  }

  return children;
}
