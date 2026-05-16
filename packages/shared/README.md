# @atlas/shared — cross-runtime types

Single source of truth for types shared between the Python backend and TypeScript frontend.

## Generation flow

```
JSON Schema (hand-authored or pulled from FastAPI's /openapi.json)
        │
        ├── Pydantic models  → apps/api/app/schemas/**
        └── TS types         → apps/web/lib/types.ts
```

To regenerate the TS types from the live API:

```bash
npx openapi-typescript http://localhost:8000/openapi.json -o apps/web/lib/types.generated.ts
```

To regenerate Pydantic schemas from JSON Schema:

```bash
datamodel-codegen --input packages/shared/schemas.json --output apps/api/app/schemas/generated.py
```

The hand-curated `types.ts` in `apps/web/lib/types.ts` extends the generated types with UI-only fields like `isNew` (ephemeral, set when an item arrives over the WebSocket).
