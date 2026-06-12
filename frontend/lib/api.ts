const BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:7860";

export interface Citation {
  source: string;
  domain: string;
  page_num: number | null;
  excerpt: string;
}

export interface QueryResponse {
  answer: string;
  key_insights: string[];
  confidence: "high" | "medium" | "low";
  citations: Citation[];
}

export interface IngestResponse {
  domain: string;
  files_ingested: number;
  chunks_indexed: number;
}

// ── Session ID ────────────────────────────────────────────────────────────────────
// Set once per page load from page.tsx; never persisted.

let _sessionId = "anonymous";

export function setSessionId(id: string): void {
  _sessionId = id;
}

function sessionHeader(): Record<string, string> {
  return { "X-Session-ID": _sessionId };
}


// ── API calls ─────────────────────────────────────────────────────────────────────

export async function fetchHealth(): Promise<void> {
  const res = await fetch(`${BASE}/api/health`);
  if (!res.ok) throw new Error("backend unreachable");
}

export async function fetchDomains(): Promise<string[]> {
  const res = await fetch(`${BASE}/api/domains`, { headers: sessionHeader() });
  if (!res.ok) throw new Error("failed to fetch domains");
  const data = await res.json();
  return data.domains as string[];
}

export async function queryDomain(
  question: string,
  domain: string
): Promise<QueryResponse> {
  const res = await fetch(`${BASE}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...sessionHeader() },
    body: JSON.stringify({ question, domain }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "unknown error" }));
    throw new Error(err.detail ?? "query failed");
  }
  return res.json();
}

export async function ingestFiles(
  domain: string,
  files: File[]
): Promise<IngestResponse> {
  const form = new FormData();
  form.append("domain", domain);
  for (const f of files) form.append("files", f);
  const res = await fetch(`${BASE}/api/ingest`, {
    method: "POST",
    headers: sessionHeader(),
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "unknown error" }));
    throw new Error(err.detail ?? "ingest failed");
  }
  return res.json();
}
