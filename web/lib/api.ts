import type { ResearchResult } from "./types";

// Strip any trailing slash so `${API_URL}/api/...` never becomes `...//api/...` (404).
const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);

export async function brief(company: string, role: string): Promise<ResearchResult> {
  const res = await fetch(`${API_URL}/api/brief`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ company, role: role.trim() || null }),
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON */
    }
    throw new Error(detail);
  }
  return res.json();
}
