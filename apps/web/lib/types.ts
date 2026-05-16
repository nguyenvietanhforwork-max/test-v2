// Atlas — frontend types. Mirrored from apps/api/app/schemas/*.py via packages/shared.

export type Region = "VN" | "INT";
export type Bucket = "macro" | "corp";
export type Confidence = "high" | "mid" | "low";

export interface Source {
  name: string;
  url: string;
}

export interface Entity {
  slug: string;
  name: string;
  ticker?: string;
  exchange?: string;
}

export interface Industry {
  slug: string;
  name: string;
  color: string;
  todayCount?: number;
}

export interface NewsItem {
  id: string;
  title: string;
  thesis: string;
  bullets: string[];
  publishedAt: string;       // ISO
  source: Source;
  industry: string;          // slug
  industries: Industry[];
  entities: Entity[];
  region: Region;
  bucket: Bucket;
  confidence: Confidence;
  rawPath: string;
  wikiPath?: string;
  isNew?: boolean;           // ephemeral, set when arrived via WS
}

export interface DailyBriefStat {
  label: string;
  value: string;
  delta?: string;
  deltaTone?: "pos" | "neg" | "neutral";
  sub?: string;
}

export interface DailyBrief {
  date: string;
  thesis: string;             // may contain <em>…</em>
  subtitle: string;
  stats: DailyBriefStat[];
}

export interface HeatmapCell {
  slug: string;
  name: string;
  color: string;
  volume: number;
  sentiment: number;
}

export interface IndustryHeatmapData {
  window: "1d" | "7d" | "30d";
  cells: HeatmapCell[];
}

export interface Report {
  id: string;
  type: "daily" | "weekly" | "master" | "industry" | "entity";
  title: string;
  publishedAt: string;
  thesis: string;
  markdown: string;
  pdfUrl?: string | null;
  version: number;
  sections: ReportSection[];
}

export interface ReportSection {
  id: string;
  heading: string;
  bodyMd: string;
  sources: { newsId: string; title: string; url: string }[];
}

export type WebSocketEvent =
  | { type: "news.created"; payload: NewsItem }
  | { type: "news.updated"; payload: NewsItem }
  | { type: "report.published"; payload: Report }
  | { type: "pipeline.step"; payload: { run_id: string; step: string; status: "started"|"done"|"failed"; latency_ms?: number; tokens?: number } }
  | { type: "pipeline.failed"; payload: { run_id: string; error: string } }
  | { type: "vault.reconciled"; payload: { added: number; updated: number; missing: number } };
