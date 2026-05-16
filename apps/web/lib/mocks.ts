// Atlas — deterministic mock data used when NEXT_PUBLIC_USE_MOCKS=true.
// Mirrors the shapes returned by the real FastAPI backend so swapping is one env var.

import type { DailyBrief, IndustryHeatmapData, NewsItem, Report } from "./types";
import { INDUSTRIES } from "./constants";

export const MOCK_BRIEF: DailyBrief = {
  date: "2026-05-15",
  thesis:
    "VN equities open at a fresh 16-month high as <em>foreign net buying</em> compounds and banks lead — but bond yields are pricing a hawkish surprise.",
  subtitle:
    "Three signals dominate the tape: (1) foreign desks added +412 B VND in five sessions, almost entirely into VCB · TCB · HPG; (2) state-owned bank capital raises are unblocked after the Q1 amendment to circular 03; (3) the SBV's overnight rate ticked to 5.45%, the highest since Dec 2024, suggesting CPI prints are concerning. Watch for the 14:00 ICT MoF auction.",
  stats: [
    { label: "Items Today", value: "23", delta: "+6 vs avg 5d", deltaTone: "pos" },
    { label: "Active Industries", value: "14/28", sub: "Banking · RE · Tech lead" },
    { label: "Sentiment Index", value: "+0.31", delta: "+0.08 vs yesterday", deltaTone: "pos" },
    { label: "Pipeline P95", value: "3.4s", sub: "embed · publish · WS push" },
  ],
};

export const MOCK_HEATMAP: IndustryHeatmapData = {
  window: "1d",
  cells: INDUSTRIES.map((i, idx) => ({
    slug: i.slug,
    name: i.name,
    color: i.color,
    volume: [8, 5, 4, 3, 2, 2, 1, 6, 4, 3, 2, 3, 1, 2, 2, 1, 1, 1, 1, 1, 2, 1, 1, 0, 1, 4, 2, 0][idx] || 0,
    sentiment: [0.4, 0.2, 0.5, 0.3, -0.1, -0.3, 0.1, 0.2, 0.1, 0.0, 0.2, 0.4, -0.1, 0.0, -0.2, 0.3, 0.1, 0.0, 0.1, -0.1, 0.0, 0.1, 0.2, 0.0, 0.1, 0.4, 0.2, 0.0][idx] || 0,
  })),
};

export const MOCK_NEWS: NewsItem[] = [
  {
    id: "n_001", title: "Vietcombank prices $1B dual-tranche issuance",
    thesis: "Vietcombank prices a $1B dual-tranche issuance at +185bps, the tightest spread by a VN bank since 2022.",
    bullets: [
      "5y at T+165, 10y at T+205 — orderbook 4.8x covered with 62% Asia ex-Japan allocation",
      "Proceeds earmarked for SME credit + green project financing under SBV circular 03 amendment",
      "Read-through positive for TCB, BIDV pipeline; spread compression suggests reopened EM HG market window",
    ],
    publishedAt: "2026-05-15T06:11:00Z",
    source: { name: "Reuters", url: "https://reuters.com/...example" },
    industry: "banking",
    industries: [{ slug: "banking", name: "Banking", color: "var(--cyan)" }],
    entities: [
      { slug: "vcb", name: "Vietcombank", ticker: "VCB", exchange: "HOSE" },
      { slug: "tcb", name: "Techcombank", ticker: "TCB", exchange: "HOSE" },
      { slug: "bid", name: "BIDV", ticker: "BID", exchange: "HOSE" },
    ],
    region: "VN", bucket: "corp", confidence: "high",
    rawPath: "raw/news/2026-05-15--reuters--vcb-issuance.md",
    wikiPath: "wiki/Vietnam Enterprises/Banking/Vietcombank.md",
    isNew: true,
  },
  {
    id: "n_002", title: "Vinhomes unlocks Long Bien phase 2",
    thesis: "Vinhomes unlocks Long Bien township phase 2, signaling a Q3 launch with 6,800 units and a step-up in pre-sales target.",
    bullets: [
      "Land use right transfer concluded last week, total GFA 1.4M sqm, ASP guided 78-92M VND/sqm",
      "Funded via VHM's March bond rollover (8.45% coupon) + JV with Capitaland on the high-rise blocks",
      "Implication: VHM 2026 pre-sales likely 105k+ B VND, beating consensus 92k; broker upgrades probable",
    ],
    publishedAt: "2026-05-15T05:48:00Z",
    source: { name: "Vneconomy", url: "https://vneconomy.vn/..." },
    industry: "real-estate",
    industries: [{ slug: "real-estate", name: "Real Estate", color: "var(--accent)" }],
    entities: [
      { slug: "vhm", name: "Vinhomes", ticker: "VHM", exchange: "HOSE" },
      { slug: "capitaland", name: "Capitaland", ticker: "CL" },
    ],
    region: "VN", bucket: "corp", confidence: "mid",
    rawPath: "raw/news/2026-05-15--vneconomy--vhm-longbien.md",
    isNew: true,
  },
  {
    id: "n_003", title: "FPT signs Japanese mega-bank core banking contract",
    thesis: "FPT books a $182M multi-year contract with a Japanese mega-bank for core banking modernization.",
    bullets: [
      "Five-year statement of work, gross margin guide 28-32% — accretive to FPT Software segment",
      "Adds to the Japan revenue base now > $1.1B run-rate, surpassing US for the first time",
      "Read-through: VN IT services premium vs. India peers narrows; CMG, KMS likely to chase mid-tier deals",
    ],
    publishedAt: "2026-05-15T07:02:00Z",
    source: { name: "Bloomberg", url: "https://bloomberg.com/..." },
    industry: "technology",
    industries: [{ slug: "technology", name: "Technology", color: "var(--violet)" }],
    entities: [{ slug: "fpt", name: "FPT Corp", ticker: "FPT", exchange: "HOSE" }],
    region: "VN", bucket: "corp", confidence: "high",
    rawPath: "raw/news/2026-05-15--bloomberg--fpt-japan.md",
  },
  {
    id: "n_004", title: "Hòa Phát Dung Quất 2 HRC line online ahead of schedule",
    thesis: "Hòa Phát commissions Dung Quất 2 HRC line ahead of schedule, raising 2026 HRC output guide to 4.2 Mt.",
    bullets: [
      "Line 1 ramped in April, line 2 ramping now — total Dung Quất 2 cap +5.6 Mt at run rate by Q4",
      "Management hints at second-half HRC ASP recovery on China stimulus + EU CBAM-linked sourcing shift",
      "Watch: HRC-iron-ore spread tightening to $312/t in May vs. $268 trough; HPG OPM should expand 250bps",
    ],
    publishedAt: "2026-05-15T06:30:00Z",
    source: { name: "CafeF", url: "https://cafef.vn/..." },
    industry: "steel",
    industries: [{ slug: "steel", name: "Steel", color: "#94A3B8" }],
    entities: [{ slug: "hpg", name: "Hòa Phát", ticker: "HPG", exchange: "HOSE" }],
    region: "VN", bucket: "corp", confidence: "mid",
    rawPath: "raw/news/2026-05-15--cafef--hpg-dq2.md",
    isNew: true,
  },
  {
    id: "n_005", title: "Fed dot plot signals fewer 2026 cuts",
    thesis: "Fed dot plot suggests two cuts in 2026, down from three — DXY breaks 105, EM FX vulnerable.",
    bullets: [
      "Powell language: 'sticky services inflation' and 'labor strength' cited twice in pressar",
      "2y UST +18bps to 4.62%, USD/JPY through 158; carry trades reawakened",
      "VN implication: SBV likely to widen rate corridor; USD/VND ceiling test at 25,500 within two weeks",
    ],
    publishedAt: "2026-05-15T03:55:00Z",
    source: { name: "FT", url: "https://ft.com/..." },
    industry: "banking",
    industries: [{ slug: "banking", name: "Banking", color: "var(--cyan)" }],
    entities: [{ slug: "fed", name: "Federal Reserve" }],
    region: "INT", bucket: "macro", confidence: "mid",
    rawPath: "raw/news/2026-05-15--ft--fed-dotplot.md",
  },
  {
    id: "n_006", title: "SBV draft circular widens foreign ownership cap",
    thesis: "SBV draft circular allows foreign ownership up to 49% for 'weak' banks under restructuring — broader than market expected.",
    bullets: [
      "Applies to CB Bank, OceanBank, GP Bank; potential strategic-investor windows for Q3 2026",
      "Korean, Singapore, Japanese banks already in due-diligence per sources",
      "Implication: VCB, BID, MBB likely to receive halo bid; SHB and HDB face de-rating risk",
    ],
    publishedAt: "2026-05-14T16:32:00Z",
    source: { name: "VnExpress", url: "https://vnexpress.net/..." },
    industry: "banking",
    industries: [{ slug: "banking", name: "Banking", color: "var(--cyan)" }],
    entities: [{ slug: "sbv", name: "SBV" }],
    region: "VN", bucket: "macro", confidence: "high",
    rawPath: "raw/news/2026-05-14--vnexpress--sbv-circular.md",
  },
];

export const MOCK_REPORTS: Report[] = [
  {
    id: "r_daily_20260515",
    type: "daily",
    title: "Daily Intelligence Brief · 2026-05-15",
    publishedAt: "2026-05-15T23:00:00Z",
    thesis: MOCK_BRIEF.thesis.replace(/<\/?em>/g, ""),
    markdown: "# Daily Intelligence Brief · 2026-05-15\n\n> **Thesis.** " + MOCK_BRIEF.thesis.replace(/<\/?em>/g, "") + "\n\n## Vietnam Corporate\n\n_Sections rendered from each NewsItem._",
    pdfUrl: "#",
    version: 1,
    sections: [
      {
        id: "s_1", heading: "Vietnam Corporate",
        bodyMd: "### Vietcombank dual-tranche\n- 5y at T+165, 10y at T+205\n- Orderbook 4.8x covered",
        sources: [{ newsId: "n_001", title: "Vietcombank prices $1B dual-tranche", url: "#" }],
      },
      {
        id: "s_2", heading: "Vietnam Macro",
        bodyMd: "### SBV foreign ownership widening\n- Up to 49% for restructuring banks\n- Halo bid for VCB · BID · MBB",
        sources: [{ newsId: "n_006", title: "SBV draft circular", url: "#" }],
      },
    ],
  },
];
