# Roadmap

Phases match `ARCHITECTURE.md §16`. Each phase has a one-line definition-of-done.

## Phase 0 — Foundations (Week 1)
- [ ] Supabase project provisioned + migrations applied
- [ ] Upstash Redis provisioned
- [ ] `services/ingestion` deployed; `/v1/ingest` reachable
- [ ] DOD: drop file → `news_items` row appears within 5s.

## Phase 1 — MVP (Week 2–3)
- [ ] Classification + summarization agents online
- [ ] n8n `ingest-news` workflow imported and active
- [ ] Daily master report (Markdown only)
- [ ] DOD: 06:00 cron produces `Processed/master/YYYY-MM-DD.md`.

## Phase 2 — Dashboard (Week 4–5)
- [ ] `apps/dashboard` deployed on Vercel
- [ ] WebSocket subscription working in prod
- [ ] Daily view + filters + trace-back panel
- [ ] DOD: ingest is visible in dashboard live, no refresh.

## Phase 3 — PDF + Search (Week 6–7)
- [ ] PDF engine deployed; master report → PDF
- [ ] Meilisearch indexed
- [ ] Hybrid search endpoint live
- [ ] DOD: sub-200ms search across 30 days.

## Phase 4 — Wiki + Graph (Week 8–9)
- [ ] Wiki enrichment agent online
- [ ] Wiki write-back worker active
- [ ] `/graph` view shows entity-news-wiki edges
- [ ] DOD: clicking a company opens a populated wiki page.

## Phase 5 — Scale (Month 3+)
- [ ] Read replica + partitioning
- [ ] Sentry + OTel + Grafana Cloud
- [ ] Multi-user RLS hardening
- [ ] DOD: p95 dashboard load <800ms at 10k items/day.
