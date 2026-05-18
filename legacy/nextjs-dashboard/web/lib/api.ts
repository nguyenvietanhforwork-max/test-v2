import type { DailyBrief, IndustryHeatmapData, NewsItem, Report } from "./types";
import { MOCK_BRIEF, MOCK_HEATMAP, MOCK_NEWS, MOCK_REPORTS } from "./mocks";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";

async function get<T>(path: string, init?: RequestInit): Promise<T> {
  if (USE_MOCKS) throw new Error("mocks-enabled"); // caller resolves below

  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    next: { revalidate: 30 },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${path} → ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  if (USE_MOCKS) throw new Error("mocks-enabled");
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

// ---------- News ----------
export async function getNewsFeed(
  params: Record<string, string | undefined>,
): Promise<{ items: NewsItem[]; nextCursor?: string }> {
  if (USE_MOCKS) {
    let items = MOCK_NEWS.slice();
    if (params.industry) items = items.filter((n) => n.industry === params.industry);
    if (params.region) items = items.filter((n) => n.region === params.region);
    if (params.bucket) items = items.filter((n) => n.bucket === params.bucket);
    return { items };
  }
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v) as [string, string][]).toString();
  return get(`/news${qs ? `?${qs}` : ""}`);
}

export async function getNewsItem(id: string): Promise<NewsItem> {
  if (USE_MOCKS) {
    const found = MOCK_NEWS.find((n) => n.id === id);
    if (!found) throw new Error("not found");
    return found;
  }
  return get(`/news/${id}`);
}

// ---------- Brief ----------
export async function getDailyBrief(date?: string): Promise<DailyBrief> {
  if (USE_MOCKS) return MOCK_BRIEF;
  return get(`/reports/daily${date ? `?date=${date}` : ""}`);
}

// ---------- Heatmap ----------
export async function getIndustryHeatmap(opts: { window: "1d" | "7d" | "30d" }): Promise<IndustryHeatmapData> {
  if (USE_MOCKS) return MOCK_HEATMAP;
  return get(`/industries/heatmap?window=${opts.window}`);
}

// ---------- Reports ----------
export async function listReports(params: { type?: string; from?: string; to?: string }) {
  if (USE_MOCKS) return { items: MOCK_REPORTS };
  const qs = new URLSearchParams(params as Record<string, string>).toString();
  const response = await get<Report[] | { items: Report[]; nextCursor?: string }>(`/reports${qs ? `?${qs}` : ""}`);
  return Array.isArray(response) ? { items: response } : response;
}

export async function getReport(id: string): Promise<Report> {
  if (USE_MOCKS) {
    const r = MOCK_REPORTS.find((x) => x.id === id) ?? MOCK_REPORTS[0];
    return r;
  }
  return get(`/reports/${id}`);
}

// ---------- Search ----------
export async function search(body: { query: string; mode?: "lexical" | "semantic" | "hybrid"; filters?: Record<string, unknown>; limit?: number }) {
  if (USE_MOCKS) return { hits: [], took_ms: 0 };
  return post(`/search`, body);
}

// ---------- Vault ----------
export async function vaultStatus() {
  if (USE_MOCKS) return { files_total: 1284, pipeline: { queue_depth: 0, dlq_count: 0 } };
  return get(`/vault/status`);
}
export async function vaultRefresh() {
  if (USE_MOCKS) return { job_id: "mock", status: "queued" };
  return post<{ job_id: string; status: string }>(`/vault/refresh`, {});
}
