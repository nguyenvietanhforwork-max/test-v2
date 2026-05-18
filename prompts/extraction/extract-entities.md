---
id: extraction/extract-entities
version: v1
model: claude-sonnet-4-6
created: 2026-05-18
last_updated: 2026-05-18
---

# Extraction — entities

Given a cleaned source document, extract a structured list of named entities.

## Input

```
{{source_text}}
```

## Output

Return JSON conforming to `schemas/semantic.schema.json#/definitions/Entity`:

```json
[
  {
    "name": "Vinhomes JSC",
    "type": "company",
    "ticker": "VHM:HOSE",
    "aliases": ["Vinhomes", "VHM"],
    "confidence": 0.95
  },
  {
    "name": "Bộ Xây dựng",
    "type": "government",
    "confidence": 0.99
  }
]
```

## Rules

- **Only the main referents of the article.** A tangentially-mentioned competitor in a comparison sentence is NOT extracted. Aim for 3–8 entities per article, not 30.
- **Resolve aliases.** If the article uses "công ty" and "doanh nghiệp" to refer to the same company, return one entity with both as aliases.
- **Confidence threshold 0.7.** Below that, omit.
- **Tickers when available.** Include exchange (HOSE / HNX / NYSE / NASDAQ).
- **No invented entities.** If an entity is referenced but not named explicitly ("a major bank"), do not invent a name.

## Notes

This prompt deliberately keeps the field surface small. Richer attribution (org chart relationships, beneficial ownership, etc.) is downstream work for the entity graph builder.
