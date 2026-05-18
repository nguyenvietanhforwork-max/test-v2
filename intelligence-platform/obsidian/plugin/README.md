# Intelligence Platform — Obsidian Plugin

Companion plugin. Optional but recommended.

## Install (dev)
1. `pnpm install && pnpm build` in this folder.
2. Copy `manifest.json` and `main.js` into `<your-vault>/.obsidian/plugins/intelligence-platform/`.
3. Enable in Obsidian → Settings → Community plugins.
4. In the plugin settings, set the API base URL.

## What it does
- **Auto-send on create:** when a new file lands in `raw/news/`, immediately POSTs it to `/v1/ingest` (skipping the 250ms filesystem-watcher debounce).
- **Command palette:**
  - "Send current note to Intelligence Platform"
  - "Open generated report for current note"

The watcher service (`services/ingestion`) remains the primary ingest path; this plugin just shortens the latency from filesystem write → API by ~250ms and lets you ingest notes from anywhere in the vault on demand.
