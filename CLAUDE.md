# CLAUDE.md — Operational instructions for AI agents working in this repository

> **Project identity:** Atlas — an AI-native intelligence infrastructure platform that combines a Research Wiki (Obsidian vault), an executive intelligence feed, AI research infrastructure, and a human-feedback learning loop.
>
> **Mental model:** `Obsidian Vault + Executive Intelligence Feed + AI Research Infrastructure + Human Feedback Loop`
>
> **Last restructure:** 2026-05-18 (v3 — hybrid architecture). See `ARCHITECTURE.md`, `outputs/audit-2026-05-18.md`, `outputs/architecture-decisions-2026-05-18.md`.

This file describes how to operate inside the repository. Authoritative content rules are in `AGENTS.md` — read it before doing anything that touches `raw/`, `wiki/`, or `Processed/` / `content/`.

---

## 1 · Repository layout (v3)

```
apps/dashboard/index.html   ← CANONICAL single-file UI (do NOT rebuild as Next.js)
apps/api/                   ← FastAPI: REST + WebSocket
content/                    ← canonical markdown intelligence artifacts (HYBRID hook)
  ├── reports/              ← daily/weekly reports
  ├── wiki/                 ← Research Wiki: concepts, entities, sources (= wiki/)
  └── _templates/
raw/                        ← IMMUTABLE. NEVER write here.
cleaned/                    ← normalized intermediates (write here)
generated/                  ← dashboard's data feed (index.json, search-index.json, graph.json, embeddings-ready.json)
feedback/                   ← human preference data (ratings.json, analytics/, datasets/)
prompts/                    ← modular prompt library (system/, extraction/, summarization/, scoring/, formatting/, evaluation/)
scripts/                    ← Python entry points + cleanup-legacy.ps1
schemas/                    ← raw / report / rating / semantic JSON Schema
packages/                   ← agents/, automation/, shared/
infra/docker/               ← Dockerfiles (api, worker, watcher, pdf)
logs/
legacy/                     ← archived retired systems (read-only)
docs/
outputs/                    ← lint reports, audits, ad-hoc exports
```

---

## 2 · Invariants (these never change)

1. **`raw/` is immutable.** Never write, never reorganize, never delete from `raw/`. New ingestion goes to `cleaned/` or `content/`. (AGENTS.md §2 is the authority.)
2. **Markdown is canonical.** `content/reports/**/*.md` are the source of truth. Postgres, Meilisearch, pgvector, `generated/*.json` are all *derived* and can be rebuilt from markdown with `python scripts/build_index.py`.
3. **One canonical dashboard.** It is `apps/dashboard/index.html`. Do NOT create a Next.js or React rewrite. The Next.js attempt is in `legacy/nextjs-dashboard/` and is intentionally retired.
4. **Modular prompts only.** Never write a monolithic prompt. Decompose into `prompts/{system,extraction,summarization,scoring,formatting,evaluation}/<name>.md` with version frontmatter.
5. **Every report carries semantic frontmatter.** See `schemas/report.schema.json` — even fields not yet consumed by downstream code must be populated. This avoids future schema migrations.
6. **`legacy/` is read-only.** It exists to preserve work that was retired. Do not modify, do not delete, do not reuse without an explicit ADR.
7. **No new infrastructure overhead.** No Kubernetes, no microservices, no service mesh, no CQRS. See ADR-010.

---

## 3 · Page types and frontmatter

Every wiki page in `content/wiki/` (or its alias `wiki/`) carries:

```yaml
---
title: Page Title
type: concept | entity | source-summary | comparison
sources:
  - raw/news/YYYY-MM-DD/filename.md
related:
  - "[[related-concept]]"
created: YYYY-MM-DD
updated: YYYY-MM-DD
confidence: high | medium | low
---
```

Every report in `content/reports/` additionally carries the full semantic surface from `schemas/report.schema.json` (entities, themes, topics, tags, related_reports, signal_score, novelty_score, embeddings_ref, prompt_version, model, template_version, generated_at).

### Naming

- Filenames: kebab-case matching the concept (e.g., `attention-mechanism.md`)
- Reports: `YYYY-MM-DD-<slug>.md`
- Cross-references: `[[wikilinks]]` for all internal links
- Source attribution: always link back to `raw/` file paths

---

## 4 · Workflows

### Ingest (markdown clipping → wiki + report)

1. Read the new source in `raw/news/YYYY-MM-DD/<slug>.md`
2. (Optional) normalize to `cleaned/YYYY-MM-DD-<slug>.md`
3. Discuss key takeaways with the user
4. Create / update `content/wiki/sources/<source-name>.md` summary
5. Create / update concept / entity pages in `content/wiki/`
6. Append the day's report `content/reports/YYYY-MM-DD-<NNN>.md`
7. Update `content/wiki/index.md`
8. Append to `content/wiki/log.md`
9. Run `python scripts/build_index.py` to refresh `generated/`

### Query

1. Read `content/wiki/index.md` to identify relevant pages
2. Read those pages + cited `raw/` sources
3. Synthesize the answer with `[[wikilinks]]` to internal pages and explicit file links to `raw/`
4. If novel and valuable, offer to save the answer as a new wiki page

### Lint

1. Scan `content/wiki/` for contradictions
2. Identify orphan pages (no incoming links)
3. Flag missing concepts referenced but not created
4. Find stale claims superseded by newer sources
5. Save results to `outputs/lint-YYYY-MM-DD.md`

### Rate / feedback

The dashboard collects ratings locally. To analyze:

1. User exports `preferences-YYYY-MM-DD.json` from the dashboard (or POSTs via `/api/v1/feedback`)
2. Place file in `feedback/inbox/` (or it lands in `feedback/ratings.json` via API)
3. Run `python scripts/analyze_feedback.py` → produces `feedback/analytics/per-prompt-version.json` etc.
4. Aggregates inform prompt iteration (update `prompts/<bucket>/<name>.md`, bump version frontmatter)

---

## 5 · The hybrid: Research Wiki ⊂ Intelligence Platform

The Research Wiki workflow (ingest / query / lint) **is** the canonical content workflow. It happens inside `content/wiki/`. The broader intelligence platform wraps the wiki with:

- A dashboard that surfaces reports (`apps/dashboard/`)
- A pipeline that auto-generates reports from raw clippings (`packages/automation/` + `scripts/`)
- A feedback loop that rates reports and feeds prompt iteration (`feedback/` + `prompts/`)
- Semantic infrastructure ready for embeddings and graph (`schemas/`, `generated/`)

Think of it as: **Research Wiki is the knowledge core; the platform is the production system around it.**

---

## 6 · What NOT to do

- Do **not** modify files in `raw/` or `legacy/`.
- Do **not** create new dashboards in HTML, Next.js, React, Svelte, or anything else. Iterate on `apps/dashboard/index.html`.
- Do **not** reintroduce Kubernetes, microservices, service mesh, CQRS, multi-region patterns. ADR-010 forbids these.
- Do **not** write monolithic prompts. Modular only.
- Do **not** treat the DB as canonical. Markdown is canonical. The DB is a cache.
- Do **not** delete files. Archive to `legacy/` instead, document in `MIGRATION.md`.

---

## 7 · Related authoritative documents

- `ARCHITECTURE.md` — system architecture (one-page)
- `AGENTS.md` — vault content rules, naming, schemas (read this before editing content)
- `outputs/audit-2026-05-18.md` — Phase 1 audit + fork resolutions
- `outputs/architecture-decisions-2026-05-18.md` — ADR-001 … ADR-011
- `MIGRATION.md` — what moved where during the v3 restructure
- `schemas/report.schema.json` — semantic surface every report must carry
- `prompts/system/identity.md` — agent identity and voice

---

*This file replaces the prior "Research Wiki" CLAUDE.md (preserved in `legacy/docs/CLAUDE-v1-research-wiki.md`). The Research Wiki framing is preserved as a subsystem inside the larger intelligence platform per ADR-001 (hybrid model).*
