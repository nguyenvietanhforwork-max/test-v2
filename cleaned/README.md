# cleaned/ — normalized intermediates between raw/ and content/

This directory holds **normalized** versions of `raw/` documents. The cleaning step strips:

- HTML / inline styling
- Web-clipper boilerplate (advertisements, navigation, "share this article" footers)
- Tracking parameters in URLs
- Encoding artifacts (zero-width spaces, smart-quote inconsistencies)
- Duplicate content from clip layout variations

…and extracts:

- Canonical URL
- Title, byline, publication date (best-effort)
- Source publication
- Language (auto-detected)
- Word count
- Reading time estimate

## File format

Each cleaned document mirrors its `raw/` source:

```
raw/news/2026-05-18/foo.md           →   cleaned/2026-05-18-foo.md
raw/PDF Files/quarterly-report.md    →   cleaned/2026-05-18-quarterly-report.md
```

Cleaned files keep `raw/` immutable; they exist so the summarization stage doesn't have to re-parse boilerplate every time.

## Lifecycle

Cleaned files are **not** the source of truth. They can be deleted at any time and regenerated with:

```bash
python scripts/clean.py
```

Schema in `schemas/cleaned.schema.json` (TBD; can derive from `raw.schema.json` + cleaning step).
