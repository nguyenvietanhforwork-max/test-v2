const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`${r.status}: ${path}`);
  return r.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`${r.status}: ${path}`);
  return r.json();
}

export const fetchDashboardToday = (on?: string) =>
  get(`/v1/dashboard/today${on ? `?on=${on}` : ""}`);

export const fetchNewsDetail = (id: string) => get(`/v1/news/${id}`);
export const fetchTraceBack = (id: string) => get(`/v1/news/${id}/trace`);
export const fetchReports = () => get<any[]>(`/v1/reports`);
export const fetchReport = (id: string) => get(`/v1/reports/${id}`);
export const fetchGraph = (entity: string | null, depth = 1) =>
  get<any>(`/v1/graph${entity ? `?entity=${encodeURIComponent(entity)}&depth=${depth}` : `?depth=${depth}`}`);
export const search = (q: string) => post<any[]>(`/v1/search`, { q, k: 20 });
export const triggerRefresh = () => post(`/v1/ingest/refresh`);
