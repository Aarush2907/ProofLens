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
          <details className="rounded-lg border border-line px-3 py-2 text-sm text-muted">
            <summary className="cursor-pointer text-foreground">How to get your keys</summary>
            <div className="mt-3 space-y-4 leading-6">
              <div>
                <p className="font-medium text-foreground">OpenAI key</p>
                <ol className="mt-1 list-decimal space-y-1 pl-5">
                  <li>
                    Sign in at{" "}
                    <a className="underline underline-offset-4" href="https://platform.openai.com" target="_blank" rel="noreferrer">
                      platform.openai.com
                    </a>
                    .
                  </li>
                  <li>
                    Add a few dollars of credit under{" "}
                    <a className="underline underline-offset-4" href="https://platform.openai.com/settings/organization/billing" target="_blank" rel="noreferrer">
                      Billing
                    </a>
                    . A key without credit cannot run research.
                  </li>
                  <li>
                    Open{" "}
                    <a className="underline underline-offset-4" href="https://platform.openai.com/api-keys" target="_blank" rel="noreferrer">
                      API keys
                    </a>{" "}
                    and choose Create new secret key.
                  </li>
                  <li>Copy it right away. It starts with sk- and is shown only once.</li>
                </ol>
              </div>
              <div>
                <p className="font-medium text-foreground">Tavily search key</p>
                <ol className="mt-1 list-decimal space-y-1 pl-5">
                  <li>
                    Create a free account at{" "}
                    <a className="underline underline-offset-4" href="https://app.tavily.com" target="_blank" rel="noreferrer">
                      app.tavily.com
                    </a>
                    .
                  </li>
                  <li>Open the dashboard and copy the API key. It starts with tvly-.</li>
                </ol>
              </div>
              <p>Paste both keys below and choose Save keys. Revoke a key from the same page whenever you want.</p>
            </div>
          </details>
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
