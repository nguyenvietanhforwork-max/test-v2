# prompts/ — modular prompt library

Per **ADR-008**, prompts are **never** monolithic. Each stage of intelligence generation has its own folder and its own versioned prompts.

## Layout

```
prompts/
├── system/         ← agent identity, voice, values
├── extraction/     ← entities, claims, structured-data extraction
├── summarization/  ← topic-sentence + bullets editorial pattern
├── scoring/        ← signal, novelty, confidence scoring
├── formatting/     ← intelligence-letter editorial style
└── evaluation/     ← quality rubric used by feedback grading
```

## Prompt file format

Every prompt file:

```markdown
---
id: summarization/topic-sentence-bullets
version: v3
model: claude-sonnet-4-6
created: 2026-04-12
last_updated: 2026-05-15
supersedes: summarization/topic-sentence-bullets@v2
evaluation_dataset: feedback/datasets/preference-pairs-2026-04.jsonl
---

# Summarization — topic sentence + supporting bullets

(prompt body in plain prose, with placeholders like {{source_text}}, {{target_length}}, etc.)

## Notes

- Reasoning behind this version
- What was changed from the prior version
- Known weaknesses
```

The pipeline reads the frontmatter to capture `prompt_version` for every generated report. That field flows to the report's frontmatter and into every rating record — closing the feedback loop on a specific prompt version.

## Versioning rules

- Patch (`@v3.1`) — wording tweaks, no behavior change
- Minor (`@v4`) — measurable behavior change, run evaluation
- Major (no convention — just a new file with `supersedes`) — rewrite

A version bump never overwrites a prior file. Old versions stay for traceability (a 2026-04-12 rating must still resolve its prompt).

## How to add a new prompt

1. Create the file under the right folder with versioned frontmatter
2. Add it to `prompts/index.md` (TBD)
3. Reference it from the pipeline code by `id@version`
4. After 50+ ratings on the new version, run `scripts/analyze_feedback.py` and compare to the previous version
