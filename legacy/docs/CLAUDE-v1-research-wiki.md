# Research Wiki: [Your Topic]

> **NOTE:** This is the original `CLAUDE.md` content, snapshotted on 2026-05-18 before the v3 restructure rewrote it. Preserved per ADR-011. The Research Wiki workflow described here is now a *subsystem* of the broader Atlas Intelligence Platform; see the new root `CLAUDE.md` for the active operational instructions.

## Project Structure

- `raw/` — Immutable source documents. Never modify files here.
- `wiki/` — LLM-generated and maintained markdown pages.
- `wiki/index.md` — Master content catalog. Update on every operation.
- `wiki/log.md` — Append-only operation log.
- `outputs/` — Generated reports, presentations, lint results.

## Page Types and Conventions

Every wiki page must have YAML frontmatter:

```yaml
---
title: Page Title
type: concept | entity | source-summary | comparison
sources:
  - raw/papers/filename.md
related:
  - "[[related-concept]]"
created: YYYY-MM-DD
updated: YYYY-MM-DD
confidence: high | medium | low
---
```

### Naming

- Filenames: kebab-case matching the concept (e.g., `attention-mechanism.md`)
- Cross-references: use `[[wikilinks]]` for all internal links
- Source references: always link back to `raw/` file paths

## Workflows

### Ingest

1. Read the source document in `raw/`
2. Discuss key takeaways with the user
3. Create `wiki/sources/[source-name].md` summary
4. Update or create concept/entity pages as needed
5. Update `wiki/index.md` with new entries
6. Append to `wiki/log.md`

### Query

1. Read `wiki/index.md` to identify relevant pages
2. Read those pages and synthesize an answer
3. Cite sources using `[[wikilinks]]`
4. If the answer is novel and valuable, offer to save it as a new wiki page

### Lint

1. Scan all wiki pages for contradictions
2. Identify orphan pages (no incoming links)
3. Flag missing concepts referenced but not created
4. Find stale claims superseded by newer sources
5. Save results to `outputs/lint-YYYY-MM-DD.md`
