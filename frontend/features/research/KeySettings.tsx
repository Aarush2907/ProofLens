"use client";

import { useState } from "react";
import { clearKeys, loadKeys, saveKeys } from "@/lib/keys";

export function KeySettings() {
  const [open, setOpen] = useState(false);
  const [openai, setOpenai] = useState(() => loadKeys().openai);
  const [search, setSearch] = useState(() => loadKeys().search);
  const [saved, setSaved] = useState(() => loadKeys().openai !== "" && loadKeys().search !== "");

  function save() {
    saveKeys({ openai, search });
    setSaved(openai.trim() !== "" && search.trim() !== "");
    setOpen(false);
  }

  function remove() {
    clearKeys();
    setOpenai("");
    setSearch("");
    setSaved(false);
  }

  return (
    <div className="rounded-xl border border-line px-4 py-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-foreground">
          API keys{" "}
          <span className={saved ? "text-sea" : "text-brass"}>{saved ? "set for this tab" : "not set"}</span>
        </p>
        <button
          type="button"
          onClick={() => setOpen((current) => !current)}
          className="text-sm text-muted underline underline-offset-4"
        >
          {open ? "Close" : "Edit keys"}
        </button>
      </div>
      {open ? (
        <div className="mt-3 space-y-3">
          <label className="block text-sm text-muted" htmlFor="openai-key">
            OpenAI API key
            <input
              id="openai-key"
              type="password"
              autoComplete="off"
              value={openai}
              onChange={(event) => setOpenai(event.target.value)}
              placeholder="sk-..."
              className="mt-1 w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm text-foreground"
            />
          </label>
          <label className="block text-sm text-muted" htmlFor="search-key">
            Tavily search API key
            <input
              id="search-key"
              type="password"
              autoComplete="off"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="tvly-..."
              className="mt-1 w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm text-foreground"
            />
          </label>
          <p className="text-xs leading-5 text-muted">
            Your keys are kept in this browser tab only and are sent with each run, so usage is billed to your own
            accounts. The server does not save them. Closing the tab removes them.
          </p>
          <div className="flex gap-3">
            <button type="button" onClick={save} className="rounded-full bg-brass px-4 py-1.5 text-sm font-medium text-ink">
              Save keys
            </button>
            <button type="button" onClick={remove} className="rounded-full border border-line px-4 py-1.5 text-sm text-foreground">
              Clear
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
