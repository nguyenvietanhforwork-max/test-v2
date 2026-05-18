# schemas/ — JSON Schemas for the canonical data surfaces

These schemas define the **shape** of every persistent artifact in the system. They are the contract that lets the markdown layer (`content/`), the derived layer (`generated/`), the dashboard, and the API all agree on what a "report" or a "rating" looks like.

## Files

| Schema | Constrains |
|---|---|
| `raw.schema.json` | The shape of a `raw/` clipping (after the Obsidian Web Clipper drops it) |
| `cleaned.schema.json` | (TBD) — shape of `cleaned/*.md` post-normalization |
| `report.schema.json` | The **full semantic surface** of a `content/reports/*.md` frontmatter. ADR-009. |
| `rating.schema.json` | Every rating record in `feedback/ratings.json`. ADR-007. |
| `semantic.schema.json` | Shared sub-schemas (entity, theme, score) referenced by report and rating. |
| `index-entry.schema.json` | One item inside `generated/index.json["items"]`. |

## Convention

- All schemas use JSON Schema draft-07.
- Schema IDs are absolute URLs anchored at `https://atlas.local/schemas/<name>.schema.json` (treated as opaque identifiers — no resolver required).
- Backward-compatible additions: add optional properties freely. Breaking changes: bump `$id` to `<name>.v2.schema.json` and migrate.
- Required fields are kept minimal; the pipeline writes everything it knows but the schema doesn't *require* fields that downstream consumers don't need yet.

## Validation

```python
import jsonschema, json, frontmatter
schema = json.load(open("schemas/report.schema.json"))
md = frontmatter.load("content/reports/2026-05-18-001.md")
jsonschema.validate(md.metadata, schema)
```

## Why JSON Schema and not Pydantic?

Pydantic models live in `apps/api/app/schemas/` and `packages/shared/`. Those are **derived** from these JSON Schemas so the API and pipeline share types, but the canonical contract is language-agnostic JSON Schema so it can validate markdown frontmatter, JSON files in `generated/`, and HTTP payloads uniformly.
