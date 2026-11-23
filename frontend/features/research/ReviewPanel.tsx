"use client";

import { useState } from "react";
import { KeySettings } from "@/features/research/KeySettings";
import { submitReview } from "@/lib/api";
import type { ResearchSession } from "@/types/api";

export function ReviewPanel({ session, onSubmitted }: { session: ResearchSession; onSubmitted: () => void }) {
  const [choices, setChoices] = useState<Record<string, "approved" | "rejected">>({});
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  if (session.stage !== "awaiting_review") {
    return null;
  }

  const ready = session.claims.every((claim) => choices[claim.id]);

  async function send(action: "continue" | "research_more") {
    setSaving(true);
    setError(null);
    try {
      await submitReview(session.id, {
        action,
        note,
        decisions:
          action === "continue"
            ? session.claims.map((claim) => ({ claim_id: claim.id, decision: choices[claim.id] }))
            : [],
      });
      onSubmitted();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The review could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section id="review" className="rounded-2xl border border-brass/40 bg-panel px-5 py-5">
      <h2 className="font-serif text-2xl text-foreground">Review the claims</h2>
      <p className="mt-2 text-sm leading-6 text-muted">
        The report is not written until you continue. Approving a claim keeps it for the writer. Rejecting a claim leaves it out of the findings. You can also send the researcher back with a note.
      </p>
      {session.claims.length === 0 ? (
        <p className="mt-4 text-sm text-muted">No claims were extracted. You can continue, and the writer will say so.</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {session.claims.map((claim) => (
            <li key={claim.id} className="rounded-xl border border-line px-4 py-3">
              <p className="text-sm leading-6 text-foreground">{claim.text}</p>
              <p className="mt-1 text-xs text-muted">{claim.verification?.status ?? "Not checked"}</p>
              <div className="mt-3 flex gap-2">
                <ChoiceButton
                  pressed={choices[claim.id] === "approved"}
                  onClick={() => setChoices((current) => ({ ...current, [claim.id]: "approved" }))}
                  label="Approve"
                />
                <ChoiceButton
                  pressed={choices[claim.id] === "rejected"}
                  onClick={() => setChoices((current) => ({ ...current, [claim.id]: "rejected" }))}
                  label="Reject"
                />
              </div>
            </li>
          ))}
        </ul>
      )}
      <label className="mt-4 block text-sm text-muted" htmlFor="review-note">
        Note for another search
        <textarea
          id="review-note"
          value={note}
          onChange={(event) => setNote(event.target.value)}
          maxLength={500}
          rows={3}
          className="mt-2 w-full rounded-xl border border-line bg-ink px-3 py-2 text-sm text-foreground"
        />
      </label>
      <div className="mt-4">
        <KeySettings />
      </div>
      {error ? <p className="mt-3 text-sm text-danger">{error}</p> : null}
      {session.error_message ? <p className="mt-3 text-sm text-danger">{session.error_message}</p> : null}
      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          disabled={saving || (session.claims.length > 0 && !ready)}
          onClick={() => void send("continue")}
          className="rounded-full bg-brass px-4 py-2 text-sm font-medium text-ink disabled:opacity-40"
        >
          {saving ? "Saving…" : "Continue to the report"}
        </button>
        <button
          type="button"
          disabled={saving || note.trim().length === 0}
          onClick={() => void send("research_more")}
          className="rounded-full border border-line px-4 py-2 text-sm text-foreground disabled:opacity-40"
        >
          Search again
        </button>
      </div>
    </section>
  );
}

function ChoiceButton({ pressed, onClick, label }: { pressed: boolean; onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={onClick}
      className={`rounded-full border px-3 py-1 text-xs uppercase tracking-wide ${
        pressed ? "border-brass bg-brass text-ink" : "border-line text-muted"
      }`}
    >
      {label}
    </button>
  );
}
