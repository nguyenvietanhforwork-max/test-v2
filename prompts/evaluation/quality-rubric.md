---
id: evaluation/quality-rubric
version: v1
model: claude-sonnet-4-6
created: 2026-05-18
last_updated: 2026-05-18
---

# Evaluation — quality rubric

Used by `scripts/analyze_feedback.py` to auto-grade reports when human ratings are sparse, and by the pipeline pre-publish to refuse low-quality reports.

## Input

```
{{report_topic_sentence}}
{{report_bullets}}
{{source_text}}
```

## Output

Return JSON with five 1..5 scores and explanations:

```json
{
  "topic_sentence_quality": 4,
  "topic_sentence_notes": "States consequence (simplification) and beneficiaries (firms + individuals). Could be more specific about magnitude.",
  "bullet_structure": 5,
  "bullet_structure_notes": "All four start with claim labels and contain specific data points.",
  "data_density": 4,
  "data_density_notes": "Three of four bullets carry specific numbers; one ('hệ quả thị trường') is qualitative.",
  "redundancy": 5,
  "redundancy_notes": "No bullet repeats the topic sentence or another bullet.",
  "confidence_calibration": 4,
  "confidence_calibration_notes": "Uses 'dự kiến' once where the magnitude is hedged appropriately.",
  "overall": 4.4,
  "publish_decision": "publish"
}
```

## Score interpretation

| Score | Meaning |
|---|---|
| 5 | Editorial-quality, no notes |
| 4 | Good with minor refinement opportunity |
| 3 | Acceptable; would benefit from regeneration but ship-able |
| 2 | Below quality bar; regenerate with feedback |
| 1 | Reject; do not publish |

## Publish decision rule

- All five scores ≥ 3 AND overall ≥ 3.5 → `publish`
- Any score ≤ 2 OR overall < 3.0 → `regenerate`
- Borderline (3.0 ≤ overall < 3.5) → `human-review`

## Calibration loop

Each week, sample 20 reports that were both auto-graded and human-rated. If rubric `overall` deviates from human `insight_quality` by more than 1.0 on average, rewrite this rubric.
