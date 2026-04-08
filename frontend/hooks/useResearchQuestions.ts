"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchResearchQuestions } from "@/lib/api";
import type { ResearchQuestion } from "@/types/api";

export function useResearchQuestions(limit: number) {
  const [questions, setQuestions] = useState<ResearchQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [requestId, setRequestId] = useState(0);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    setRequestId((current) => current + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const next = await fetchResearchQuestions(limit);
        if (cancelled) {
          return;
        }
        setQuestions(next);
        setError(null);
      } catch (caught) {
        if (cancelled) {
          return;
        }
        const message =
          caught instanceof Error ? caught.message : "Saved questions could not be loaded.";
        setError(message);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [limit, requestId]);

  return { questions, loading, error, reload };
}
