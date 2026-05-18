# content/ — canonical intelligence artifacts

Per **ADR-006**, markdown in this folder is the **canonical** source of truth for the platform. Everything else (Postgres rows, Meilisearch documents, pgvector embeddings, the JSON files in `generated/`) is *derived* from these markdown files.

## Layout

```
content/
├── reports/        ← daily + weekly intelligence reports
├── wiki/           ← Research Wiki: concepts, entities, sources (hybrid alias for /wiki)
└── _templates/     ← markdown templates
```

## Hybrid alias

`content/wiki/` and the repo-root `wiki/` are conceptually the same content. Albert chose the hybrid model (ADR-001) where the existing Research Wiki workflow is preserved as a subsystem rather than physically moved (a physical move would break every `[[wikilink]]` and every frontmatter `sources:` reference).

**Treat them as one folder.** When tooling needs a path, `wiki/` is the canonical OS path. `content/wiki/` is the conceptual name in documentation and ADRs.

For new tooling: prefer `wiki/` (no symlink required, no Windows symlink-permission issues).

## Reports vs. wiki — semantic difference

| | `content/wiki/` | `content/reports/` |
|---|---|---|
| **Audience** | Knowledge graph (concepts, entities) | Executive intelligence feed |
| **Cadence** | Updated continuously as new sources arrive | Generated daily / weekly |
| **Schema** | Lightweight YAML frontmatter (`type`, `sources`, `related`, `confidence`) | Full semantic schema — see `schemas/report.schema.json` |
| **Lifecycle** | Long-lived, edited many times | Append-only — superseded by newer reports |
| **Authored by** | AI + human review | AI only, with feedback-driven prompt tuning |

## Workflows

See `CLAUDE.md` §4 for ingest/query/lint/rate workflows.

## Templates

`_templates/` (= `_templates/` at repo root) holds the markdown templates referenced by `AGENTS.md`. New report and wiki page types must register a template there.
