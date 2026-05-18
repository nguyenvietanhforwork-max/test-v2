# apps/dashboard/ — canonical single-file dashboard

Per **ADR-002**, this is the **one** canonical dashboard. Albert chose `news-dashboard-v2.html` as the MVP; this folder holds its canonical copy.

## Files

| File | Source | Purpose |
|---|---|---|
| `index.html` | populated by `scripts/cleanup-legacy.ps1 -Apply` (or copied manually from `../../news-dashboard-v2.html`) | The canonical dashboard. ~2300 lines. Self-contained. |
| `README.md` | this file | |

## Why a single file

The platform's spec mandates "simplicity first" and "remove giant static HTML architecture" — but for the MVP, a single VnEconomy-styled HTML page with inlined data is *simpler* than a Next.js build pipeline, not more complex. The dashboard:

- Has zero dependencies (Google Fonts only)
- Runs from `file://` for instant preview
- Deploys to Vercel as a static asset
- Carries its own data (`const ITEMS = [...]`) until the markdown pipeline catches up

When `generated/index.json` is populated by `scripts/build_index.py`, the dashboard's bootstrap code can `fetch("/generated/index.json")` and replace the inlined ITEMS. The inlined version stays as a robust fallback.

## What this dashboard does

1. **Renders ~30 article cards** with topic + industry chips, title, lede, source link
2. **Topic filtering** — vimo-vn, vimo-global, enterprise-vn, enterprise-global with industry sub-filters
3. **AI mini-reports** — each card expands to topic_sentence + 3-4 bullet supporting ideas (matches `prompts/summarization/topic-sentence-bullets.md`)
4. **4-criteria rating** — data density, insight quality, writing style, length appropriateness (matches `schemas/rating.schema.json`)
5. **Tag-based feedback** — user adds free-form tags (e.g. "buried lede", "great context")
6. **`preferences.json` export** — downloads all ratings as `preferences-YYYY-MM-DD.json` for later analysis by `scripts/analyze_feedback.py`
7. **Daily Brief generator** — opens a printable executive brief in a new tab (Save-as-PDF compatible)
8. **Vercel sync button** — pings a deploy hook to rebuild the static site
9. **`localStorage` persistence** — ratings survive across reloads

## Deployment (Vercel static)

`vercel.json` at repo root is configured to serve `apps/dashboard/` as the static site. No build step required.

```json
{
  "outputDirectory": "apps/dashboard",
  "framework": null
}
```

## Iterating on the dashboard

- **CSS / layout / type:** edit the `<style>` block at the top
- **Data source:** the `const ITEMS = [...]` array is the single source until `generated/index.json` is wired
- **Rating logic:** see lines ~1960–2185 — they are the canonical implementation of the rating UI and `preferences.json` shape (which mirrors `schemas/rating.schema.json`)
- **Vercel hook:** the `VERCEL_DEPLOY_HOOK` constant near the top is where the deploy webhook URL goes

## Forbidden refactors

Per ADR-002, do **not**:
- Rebuild this as a Next.js / React / Svelte / Vue app
- Split it across multiple files prematurely (CSS, JS, HTML all stay together for MVP)
- Replace the inlined ITEMS array before `generated/index.json` is reliably populated

Iteration is welcome; replacement is not.
