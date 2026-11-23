// The visitor's own API keys. They stay in this browser tab (sessionStorage),
// are sent as request headers, and are never put in a URL or sent anywhere
// except the ProofLens API.

const OPENAI = "prooflens.openaiKey";
const SEARCH = "prooflens.searchKey";

export type ApiKeys = { openai: string; search: string };

function store(): Storage | null {
  try {
    return globalThis.sessionStorage ?? null;
  } catch {
    return null;
  }
}

export function loadKeys(): ApiKeys {
  const area = store();
  return {
    openai: area?.getItem(OPENAI) ?? "",
    search: area?.getItem(SEARCH) ?? "",
  };
}

export function saveKeys(keys: ApiKeys): void {
  const area = store();
  if (!area) {
    return;
  }
  area.setItem(OPENAI, keys.openai.trim());
  area.setItem(SEARCH, keys.search.trim());
}

export function clearKeys(): void {
  const area = store();
  area?.removeItem(OPENAI);
  area?.removeItem(SEARCH);
}

export function keyHeaders(): Record<string, string> {
  const keys = loadKeys();
  const headers: Record<string, string> = {};
  if (keys.openai) {
    headers["X-OpenAI-Key"] = keys.openai;
  }
  if (keys.search) {
    headers["X-Search-Key"] = keys.search;
  }
  return headers;
}
