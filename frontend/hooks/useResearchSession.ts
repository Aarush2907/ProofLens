"use client";

import { useEffect, useState } from "react";
import { fetchResearchSession } from "@/lib/api";
import type { ResearchSession } from "@/types/api";

const POLL_MS = 4000;

export function useResearchSession(id: string) {
  const [session, setSession] = useState<ResearchSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [requestId, setRequestId] = useState(0);

  const reload = () => {
    setLoading(true);
    setError(null);
    setRequestId((current) => current + 1);
  };

  useEffect(() => {
    let cancelled = false;
    let timer = 0;

    async function load() {
      try {
        const next = await fetchResearchSession(id);
        if (cancelled) {
          return;
        }
        setSession(next);
        setError(null);
        if (next.status === "running") {
          timer = window.setTimeout(() => {
            void load();
          }, POLL_MS);
        }
      } catch (caught) {
        if (cancelled) {
          return;
        }
        const message = caught instanceof Error ? caught.message : "That research run could not be loaded.";
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
      window.clearTimeout(timer);
    };
  }, [id, requestId]);

  return { session, loading, error, reload };
}
