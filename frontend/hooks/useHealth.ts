"use client";

import { useEffect, useState } from "react";
import { fetchHealth } from "@/lib/api";
import type { HealthReport } from "@/types/api";

const POLL_MS = 20000;

export function useHealth() {
  const [report, setReport] = useState<HealthReport | null>(null);
  const [unreachable, setUnreachable] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const next = await fetchHealth();
        if (!cancelled) {
          setReport(next);
          setUnreachable(false);
        }
      } catch {
        if (!cancelled) {
          setReport(null);
          setUnreachable(true);
        }
      }
    }

    void load();
    const timer = window.setInterval(() => {
      void load();
    }, POLL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  return { report, unreachable };
}
