"use client";

import { useEffect, useState } from "react";
import { apiUrl } from "@/lib/api";
import type { ActivityEvent } from "@/types/api";

export type StreamConnection = "connecting" | "live" | "reconnecting" | "closed";

export function useActivityStream(sessionId: string) {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [connection, setConnection] = useState<StreamConnection>("connecting");

  useEffect(() => {
    const source = new EventSource(`${apiUrl()}/api/research/${sessionId}/events`);
    let opened = false;

    source.onopen = () => {
      opened = true;
      setConnection("live");
    };

    source.onmessage = (message) => {
      let event: ActivityEvent;
      try {
        event = JSON.parse(message.data) as ActivityEvent;
      } catch {
        return;
      }
      if (typeof event.id !== "number" || typeof event.message !== "string") {
        return;
      }
      setEvents((current) => (current.some((item) => item.id === event.id) ? current : [...current, event]));
      if (event.terminal) {
        source.close();
        setConnection("closed");
      }
    };

    source.onerror = () => {
      if (source.readyState === EventSource.CLOSED) {
        setConnection("closed");
        return;
      }
      setConnection(opened ? "reconnecting" : "connecting");
    };

    return () => {
      source.close();
    };
  }, [sessionId]);

  const latest = events.length > 0 ? events[events.length - 1] : null;
  return { events, latest, connection };
}
