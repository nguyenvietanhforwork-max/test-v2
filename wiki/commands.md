---
title: Commands
type: cheatsheet
updated: 2026-05-13
---

# Pipeline Commands

Copy-paste these into Claude Code (or any LLM agent with file access to this vault) to run the pipeline defined in [[../agent|agent.md]]. The agent reads `CLAUDE.md` + `agent.md` automatically when invoked in this directory.

## Ingest a new source

Drop the file into the matching `raw/` subfolder, then:

```
Please ingest the new files in raw/. Follow the Ingest workflow in agent.md:
detect → fingerprint → triage (ask me before each) → extract → normalize → stage.
For each new file show me title, kind, slug, one-line preview, and wait for my
go/skip decision before extracting.
```

## Link & publish staged sources

After ingest, the source is in state `summarized`. To advance to `published` and create the cascading wiki pages:

```
Link and publish every staged source. For each, create wiki/sources/<slug>.md
from the source-summary template, then create or update concept and entity
pages it references. Update wiki/index.md and append to wiki/log.md.
```

## Query

```
Query: WHAT YOU WANT TO KNOW?

Read wiki/index.md, identify the relevant pages, read them, and synthesize an
answer with [[wikilink]] citations. If the answer is novel and worth keeping,
offer to save it as a new comparison or concept page.
```

## Build dashboard + report

```
Build. Run the Build operation from agent.md:
1. Walk wiki/ and raw/
2. Compute KPIs, quality scores, graph
3. Write outputs/dashboard.html, outputs/dashboard-data.json
4. Write outputs/report-YYYY-MM-DD.md
5. Write outputs/graph.json, outputs/graph.mmd, outputs/timeline.json
6. Append a build row to wiki/log.md
Report the file paths and a 2–3 sentence summary.
```

## Full rebuild

```
Build --full. Clear .cache/extracts, .cache/summaries, .cache/entities and
re-run the full pipeline from raw/. Preserve .cache/fingerprints.json.
```

## Lint

```
Lint the wiki. Save the result to outputs/lint-YYYY-MM-DD.md. Cover:
contradictions, orphan pages, stale pages, un-ingested raw sources,
missing concepts referenced but not created, duplicate titles.
```

## Consolidate memory (occasional)

```
Consolidate. Walk every wiki page, merge near-duplicates, normalize aliases,
collapse any concept page with <50 words into its parent, then regenerate
wiki/index.md. Log every change to wiki/log.md.
```
