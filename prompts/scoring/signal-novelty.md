---
id: scoring/signal-novelty
version: v1
model: claude-sonnet-4-6
created: 2026-05-18
last_updated: 2026-05-18
---

# Scoring — signal & novelty

Given a finished report (topic sentence + bullets) and the prior 30 days of reports on the same theme, return two 0..1 scores.

## Input

```
{{report_topic_sentence}}
{{report_bullets}}
{{prior_reports_summary}}   # last 30 days, same theme, topic_sentence + date
```

## Output

```json
{
  "signal_score": 0.78,
  "signal_rationale": "Implements a regulatory change that was previously only signaled in committee meetings; affects ~12,000 active construction firms.",
  "novelty_score": 0.41,
  "novelty_rationale": "The administrative-simplification narrative has been ongoing for 6 months; this report adds specificity but not a new frame."
}
```

## Scoring rubric

**Signal** (`0..1`): how much this report changes an informed reader's view or actions.
- 0.0 — repeats what the reader already knew, no new datapoint
- 0.3 — confirms a prior belief with new data
- 0.6 — meaningful update; the reader updates a model
- 0.85 — material change; the reader changes a position or strategy
- 1.0 — transformative; the reader's macro view shifts

**Novelty** (`0..1`): how non-obvious or unexpected.
- 0.0 — widely reported obvious news
- 0.3 — well-covered but with a slightly new detail
- 0.6 — a real angle not in the mainstream feed
- 0.85 — surfaces something most readers wouldn't have noticed
- 1.0 — genuinely new — first to report or first to frame

Signal and novelty are **independent**. A widely-reported but transformative news event scores high signal, low novelty. A clever angle on a small event scores low signal, high novelty.

## Calibration

After every 100 reports, compare model scores to actual user ratings (`feedback/analytics/per-prompt-version.json`). If model `signal_score` correlates < 0.4 with user `insight_quality` rating, rewrite this prompt.
