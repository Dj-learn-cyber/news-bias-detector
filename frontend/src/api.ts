import type { AnalyzeResponse } from "./types";

export async function analyzeArticle(payload: {
  text?: string;
  url?: string;
}): Promise<AnalyzeResponse> {
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed: ${res.status}`);
  }

  return res.json();
}
