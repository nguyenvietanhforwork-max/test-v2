# legacy/ — Archived retired systems

This directory holds systems retired during the **v3 restructure (2026-05-18)**. Per ADR-011, nothing is destroyed; everything human-written is archived here for recovery.

> **`legacy/` is read-only.** Do not modify files inside it. To revive a retired system, copy/move it back to the root with an explicit ADR.

## Contents (populated by `scripts/cleanup-legacy.ps1`)

| Path | What it is | Why retired |
|---|---|---|
| `intelligence-platform/` | Complete parallel monorepo (its own apps/api, apps/dashboard, services/, infra/, n8n/, Obsidian plugin, Supabase migrations, Railway configs). | Duplicate of `apps/` + `packages/`. ADR-001 / -003 / -004. |
| `nextjs-dashboard/web/` | Next.js 14 dashboard, React 19, Tailwind, shadcn/ui, real component code. | Albert chose `news-dashboard-v2.html` as the canonical MVP. ADR-002. |
| `v1-dashboard/` | Original single-file `index.html` + `news_database.json` + soulslab variant + three generated dashboards (atlas-dashboard.html, dashboard.html, sync-dashboard.html). | Replaced by `apps/dashboard/index.html`. ADR-002. |
| `static-html/` | `demo-dashboard.html`, `demo-folder/`, `offline-trials/` (5 prototypes). | Experimental dashboards. ADR-002. |
| `k8s/` | Kubernetes namespace, deployments, ingress manifests. | ADR-010 forbids Kubernetes. |
| `deploy-alternates/` | `fly.toml`, `api-Procfile`, `api-railway.json`. | One prod target only (Render). ADR-005. |
| `root-scripts/` | `process_news.py`, `generate.py`, `process_news_agent.py`. | Superseded by `packages/automation/` + `scripts/`. ADR-004. |
| `prompts-archive/` | Six historical prompt/spec markdown files + the zipped prompt bundle. | Replaced by modular `prompts/`. ADR-008. |
| `docs/` | `CLAUDE-v1-research-wiki.md` (the prior CLAUDE.md before this restructure rewrote it). | Snapshot preservation. |
| `duplicates/` | Reserved for ad-hoc duplicate-file archiving. | |

## How to recover something

```powershell
# Example: bring back the Next.js dashboard for reference
Copy-Item -Path .\legacy\nextjs-dashboard\web\ -Destination .\reference-nextjs\ -Recurse

# Example: revive a deployment alt
Move-Item -Path .\legacy\deploy-alternates\fly.toml -Destination .\fly.toml
```

## How to permanently delete

Only after explicit user confirmation and at least one full backup:

```powershell
Remove-Item -Path .\legacy\<subdir>\ -Recurse -Force
```

Even then, prefer to leave `legacy/` intact. Disk is cheap; rebuilding is not.

## Authoritative documents

- `../MIGRATION.md` — full list of moves, what each was replaced by
- `../outputs/audit-2026-05-18.md` — Phase 1 audit
- `../outputs/architecture-decisions-2026-05-18.md` — ADR-001 … ADR-011 explaining every retirement
