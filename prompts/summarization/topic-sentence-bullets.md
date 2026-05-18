---
id: summarization/topic-sentence-bullets
version: v3
model: claude-sonnet-4-6
created: 2026-04-12
last_updated: 2026-05-18
evaluation_dataset: feedback/datasets/preference-pairs-2026-04.jsonl
---

# Summarization — topic sentence + supporting bullets

The editorial pattern used by the v2 dashboard's mini-reports. **Match the existing ITEMS in `news-dashboard-v2.html`** as the gold standard — they were hand-crafted by Albert and reflect his preferred style.

## Input

```
{{source_title}}
{{source_text}}
{{target_word_count = 220}}    # 4 bullets × ~50 words each + topic sentence
```

## Output

Return JSON matching `schemas/report.schema.json#/properties/mini_report`:

```json
{
  "topic_sentence": "(one sentence — see rules)",
  "bullets": [
    "<b>Tên luận điểm:</b> (specific data / context / consequence)",
    "<b>Tên luận điểm:</b> ...",
    "<b>Tên luận điểm:</b> ...",
    "<b>Tên luận điểm:</b> ..."
  ]
}
```

## Topic-sentence rules

The first sentence is a *thesis*, not a re-statement of the headline. It tells the reader **what changed** and **why it matters**, in one breath. Pattern:

> {agent} {action} {object}, {immediate consequence / why it matters}.

- ❌ Bad: "Bộ Xây dựng công bố sửa đổi 4 thủ tục hành chính." (just re-states the headline)
- ✅ Good: "Bộ Xây dựng sửa đổi 4 thủ tục hành chính nhằm đơn giản hóa quy trình cấp phép và chứng chỉ hành nghề cho cá nhân, tổ chức trong lĩnh vực xây dựng." (says *why* — simplification, who benefits)

## Bullet rules

3–6 bullets, ideally 4. Each bullet:

1. Starts with `<b>Tên luận điểm:</b>` — a 2–5-word claim label
2. Then a concrete sentence: data, context, or consequence
3. Specific numbers (%, billions VND, USD, YoY) — these get auto-highlighted in the UI
4. No bullet repeats the topic sentence

Cover, in this order when applicable:
1. **Scope / what's changing** — what's actually different now
2. **Mechanism / how** — the lever being pulled
3. **Beneficiaries / who's affected** — companies, sectors, demographics
4. **Market consequence** — what to expect downstream

## Voice

Per `prompts/system/identity.md`. Vietnamese sources → Vietnamese output, editorial register.

## Common failure modes (auto-graded by `prompts/evaluation/quality-rubric.md`)

- Topic sentence is a recap of the headline → fail "topic-sentence"
- Bullets start with a character/event narrative instead of claim → fail "bullet-structure"
- No specific numbers anywhere → fail "data-density"
- Five bullets that all say variations of "this is good for the sector" → fail "redundancy"
- Hedge words on every claim → fail "confidence-calibration"
