"""
scripts/summarize.py — cleaned/ → content/reports/.

For each cleaned document:
  1. Run extraction (entities) — prompts/extraction/extract-entities.md
  2. Run classification (theme, industry) — prompts/extraction/* (TBD)
  3. Run summarization (topic_sentence + bullets) — prompts/summarization/topic-sentence-bullets.md
  4. Run scoring (signal, novelty) — prompts/scoring/signal-novelty.md
  5. Format as intelligence-letter — prompts/formatting/intelligence-letter.md
  6. Write to content/reports/YYYY-MM-DD-<slug>.md with full semantic frontmatter

USAGE
    python scripts/summarize.py                           # process all unsummarized cleaned/
    python scripts/summarize.py --date 2026-05-18         # only that date
    python scripts/summarize.py --file cleaned/foo.md     # specific file
    python scripts/summarize.py --dry-run                 # print the report, don't write
    python scripts/summarize.py --force                   # re-summarize even if content/reports/ output exists

When ANTHROPIC_API_KEY is set the script calls Claude (model = $DEFAULT_MODEL,
default `claude-sonnet-4-6`) using the prompt files under `prompts/`. Without
the key it falls back to a schema-valid stub so the rest of the pipeline can
still be exercised end-to-end (build_index → graph → dashboard cards).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import unicodedata
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CLEANED = REPO_ROOT / "cleaned"
CONTENT_REPORTS = REPO_ROOT / "content" / "reports"
PROMPTS = REPO_ROOT / "prompts"

TEMPLATE_VERSION = "intelligence-letter@v2"
PROMPT_VERSION = "summarization/topic-sentence-bullets@v3"
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "claude-sonnet-4-6")
MAX_BODY_CHARS = 12000  # truncate very long sources so the LLM call stays bounded


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9-]+", "-", s).strip("-").lower()
    return s[:60] or "report"


def _load_cleaned(path: pathlib.Path) -> tuple[dict[str, str], str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    fm: dict[str, str] = {}
    body = raw
    if raw.startswith("---"):
        try:
            _, fm_block, body = raw.split("---", 2)
            in_orig = False
            orig_indent = None
            for line in fm_block.splitlines():
                stripped = line.strip()
                # Detect the start of the commented-out original frontmatter block
                if stripped.startswith("# original frontmatter"):
                    in_orig = True
                    continue
                if in_orig:
                    # Lines look like '#   title: "..."'  -- pull title/source/description if present
                    if not stripped.startswith("#"):
                        in_orig = False
                    else:
                        inner = stripped.lstrip("#").strip()
                        if ":" in inner:
                            k, _, v = inner.partition(":")
                            key = k.strip()
                            val = v.strip().strip('"')
                            if key in ("title", "source", "description", "published", "created") and key not in fm:
                                fm["orig_" + key] = val
                        continue
                if stripped.startswith("#") or ":" not in stripped:
                    continue
                k, _, v = stripped.partition(":")
                fm[k.strip()] = v.strip().strip('"')
        except ValueError:
            pass
    return fm, body.strip()


def _read_prompt(rel_path: str) -> str:
    """Read prompts/<rel_path> and strip frontmatter so only the body is returned."""
    p = PROMPTS / rel_path
    if not p.exists():
        return ""
    text = p.read_text(encoding="utf-8")
    if text.startswith("---"):
        try:
            _, _fm, body = text.split("---", 2)
            return body.strip()
        except ValueError:
            return text
    return text


# stub fallback

def _llm_pipeline_stub(body: str, reason: str = "no API key configured") -> dict[str, Any]:
    """Schema-valid placeholder used when the real LLM call is unavailable.

    The topic_sentence + each bullet meet the minLength constraints in
    schemas/report.schema.json so build_index --validate-only still passes.
    """
    return {
        "entities": [],
        "themes": [],
        "topics": [],
        "industry": "",
        "geography": [],
        "mini_report": {
            "topic_sentence": (
                "(stub - " + reason + "; wire ANTHROPIC_API_KEY or check the LLM call. "
                "This card will populate on the next pipeline run.)"
            ),
            "bullets": [
                "<b>Stub mode:</b> the pipeline ran without a real LLM response (" + reason + ").",
                "<b>Next step:</b> set ANTHROPIC_API_KEY in CI secrets (GitHub Actions) or in .env locally.",
                "<b>Prompt used:</b> prompts/summarization/topic-sentence-bullets.md defines the editorial pattern.",
            ],
        },
        "signal_score": None,
        "novelty_score": None,
        "confidence": "low",
    }


# real Anthropic call

_OUTPUT_TEMPLATE = """
Return EXACTLY ONE JSON object - no markdown fence, no commentary before or after.
Schema (minLength rules MUST be met, otherwise the report is rejected):

{
  "topic_sentence": "string, >= 40 chars, follows topic-sentence rules above (thesis, not headline-recap)",
  "bullets": [
    "<b>Ten luan diem:</b> sentence... (>= 20 chars; 3-6 bullets total)",
    "<b>Ten luan diem:</b> ...",
    "<b>Ten luan diem:</b> ..."
  ],
  "entities": [
    {"name": "string", "type": "company|government|person|location|sector|organization", "confidence": 0.9}
  ],
  "industry": "single short slug e.g. real-estate | construction | agriculture | finance | energy | manufacturing | tech | trade | macro (empty if not classifiable)",
  "themes": ["short string", "..."],
  "topics": ["short string", "..."],
  "geography": ["Vietnam", "..."],
  "signal_score": 0.0,
  "novelty_score": 0.0,
  "confidence": "high|medium|low"
}
"""


def _build_user_prompt(title: str, body: str) -> str:
    sum_prompt = _read_prompt("summarization/topic-sentence-bullets.md")
    ent_prompt = _read_prompt("extraction/extract-entities.md")
    score_prompt = _read_prompt("scoring/signal-novelty.md")

    body_trimmed = body[:MAX_BODY_CHARS]
    if len(body) > MAX_BODY_CHARS:
        body_trimmed += "\n\n[... source truncated for prompt-size budget ...]"

    parts = [
        "You are processing a single news article. Produce ONE structured intelligence-letter "
        "card by applying the rules below. Vietnamese sources -> Vietnamese output (editorial register).",
        "",
        "================== SUMMARIZATION RULES ==================",
        sum_prompt,
        "",
        "================== ENTITY EXTRACTION RULES ==================",
        ent_prompt,
        "",
        "================== SIGNAL / NOVELTY RULES ==================",
        score_prompt,
        "",
        "================== ARTICLE TITLE ==================",
        title,
        "",
        "================== ARTICLE BODY ==================",
        body_trimmed,
        "",
        "================== OUTPUT ==================",
        _OUTPUT_TEMPLATE.strip(),
    ]
    return "\n".join(parts)


def _llm_pipeline_real(title: str, body: str) -> dict[str, Any]:
    """Call Anthropic Messages API. Returns the same dict shape as the stub.

    Raises on any error - caller is expected to fall back to stub.
    """
    import anthropic  # imported lazily so script still runs without the SDK

    system = _read_prompt("system/identity.md")
    user_msg = _build_user_prompt(title, body)

    client = anthropic.Anthropic()  # picks up ANTHROPIC_API_KEY from env
    resp = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )

    # Concatenate any text blocks (Anthropic SDK 0.40+ returns a list)
    text = ""
    for block in resp.content:
        t = getattr(block, "text", None)
        if t:
            text += t

    # Strip code fences if the model wrapped JSON in ```json ... ```
    fence = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    candidate = fence.group(1) if fence else text

    # Fall back to first {...} block if there's still surrounding prose
    m = re.search(r"\{[\s\S]*\}", candidate)
    if not m:
        raise ValueError("LLM response contained no JSON object. First 200 chars: " + repr(text[:200]))
    data = json.loads(m.group(0))

    # Normalize to internal shape; tolerate missing keys
    return {
        "entities": data.get("entities") or [],
        "themes": data.get("themes") or [],
        "topics": data.get("topics") or [],
        "industry": data.get("industry") or "",
        "geography": data.get("geography") or [],
        "mini_report": {
            "topic_sentence": (data.get("topic_sentence") or "").strip(),
            "bullets": [b for b in (data.get("bullets") or []) if isinstance(b, str) and b.strip()],
        },
        "signal_score": data.get("signal_score"),
        "novelty_score": data.get("novelty_score"),
        "confidence": data.get("confidence") or "medium",
    }


def _format_anthropic_error(e: Exception) -> str:
    """Pull as much detail as possible from an Anthropic SDK error for CI logs."""
    parts = [type(e).__name__]
    msg = str(e)
    if msg:
        parts.append(msg[:400])
    # SDK 0.40+ attaches .status_code + .body / .response
    for attr in ("status_code", "code"):
        val = getattr(e, attr, None)
        if val is not None:
            parts.append(f"{attr}={val}")
    body = getattr(e, "body", None)
    if body is None:
        resp = getattr(e, "response", None)
        if resp is not None:
            try:
                body = resp.text
            except Exception:
                body = repr(resp)[:300]
    if body is not None:
        parts.append("body=" + str(body)[:500])
    return " | ".join(parts)


# Models to try in order. The first is the "best" model from $DEFAULT_MODEL.
# If Anthropic rejects it (bad model name, capacity), fall through to known-good
# date-stamped names. This makes summarize.py resilient to API model-string changes.
_FALLBACK_MODELS = [
    "claude-sonnet-4-5-20250929",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest",
]


def _llm_pipeline(title: str, body: str) -> dict[str, Any]:
    """Dispatch: real LLM if ANTHROPIC_API_KEY is set, else schema-valid stub."""
    global DEFAULT_MODEL
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return _llm_pipeline_stub(body, reason="ANTHROPIC_API_KEY not set")

    # Build model trial list: primary first, then fallbacks (dedup, keep order)
    primary = os.environ.get("DEFAULT_MODEL", DEFAULT_MODEL)
    trial = []
    for m in [primary] + _FALLBACK_MODELS:
        if m and m not in trial:
            trial.append(m)

    last_err: str = ""
    for idx, model in enumerate(trial):
        # Mutate module-global so _llm_pipeline_real picks up the model
        DEFAULT_MODEL = model
        try:
            result = _llm_pipeline_real(title, body)
            if idx > 0:
                print("  + LLM succeeded on fallback model: " + model, file=sys.stderr)
            break
        except ImportError as e:
            print("  ! anthropic SDK not installed (" + str(e) + ") - using stub", file=sys.stderr)
            return _llm_pipeline_stub(body, reason="anthropic SDK missing")
        except Exception as e:  # noqa: BLE001 - fail soft per model trial
            detail = _format_anthropic_error(e)
            last_err = detail
            print("  ! LLM attempt " + str(idx + 1) + "/" + str(len(trial)) + " (" + model + ") failed: " + detail, file=sys.stderr)
            # On BadRequest with invalid model name, try next model.
            # On other errors (auth, network), still try next as a best effort.
            continue
    else:
        # All trials exhausted
        print("  ! All LLM models failed - using stub. Last: " + last_err, file=sys.stderr)
        return _llm_pipeline_stub(body, reason="LLM call failed (all models)")

    # Post-validate: if the model produced an empty or too-short response, fall back.
    mr = result["mini_report"]
    if (
        not mr["topic_sentence"]
        or len(mr["topic_sentence"]) < 40
        or len(mr["bullets"]) < 3
    ):
        print(
            "  ! LLM returned content below schema minLength - using stub. "
            "(topic_sentence len=" + str(len(mr["topic_sentence"])) + ", bullets=" + str(len(mr["bullets"])) + ")",
            file=sys.stderr,
        )
        return _llm_pipeline_stub(body, reason="LLM output failed minLength check")
    return result


# report writer

def summarize_one(cleaned_path: pathlib.Path, *, dry_run: bool = False, force: bool = False) -> pathlib.Path | None:
    fm, body = _load_cleaned(cleaned_path)

    date = fm.get("cleaned_at", datetime.now(timezone.utc).isoformat())[:10]
    # Title displayed in frontmatter -- prefer the original Vietnamese title from raw/.
    title = fm.get("orig_title") or fm.get("title") or cleaned_path.stem.replace("-", " ").title()
    # Slug used in filename / id -- keep the SAME algorithm previously-committed reports used,
    # so a regen overwrites in place rather than creating orphans.
    slug_basis = fm.get("title") or cleaned_path.stem.replace("-", " ").title()
    slug = _slug(slug_basis)
    report_id = "report-" + date + "-" + slug
    out_path = CONTENT_REPORTS / (date + "-" + slug + ".md")

    # Skip if a non-stub report already exists. A regen is forced when the previous
    # output was just a stub (e.g. an earlier CI run had no ANTHROPIC_API_KEY).
    if out_path.exists() and not force and not dry_run:
        try:
            existing = out_path.read_text(encoding="utf-8", errors="replace")
            if "(stub" not in existing[:600] and "<b>Stub mode:</b>" not in existing[:1500]:
                print("  . skip (exists): " + str(out_path.relative_to(REPO_ROOT)), file=sys.stderr)
                return None
        except OSError:
            pass

    pipeline = _llm_pipeline(title, body)

    frontmatter = {
        "id": report_id,
        "type": "report",
        "kind": "daily-brief",
        "date": date,
        "title": title,
        "sources": [fm.get("source_path", str(cleaned_path.relative_to(REPO_ROOT)).replace("\\", "/"))],
        "industry": pipeline["industry"],
        "themes": pipeline["themes"],
        "topics": pipeline["topics"],
        "geography": pipeline["geography"],
        "entities": pipeline["entities"],
        "signal_score": pipeline["signal_score"],
        "novelty_score": pipeline["novelty_score"],
        "confidence": pipeline["confidence"],
        "prompt_version": PROMPT_VERSION,
        "model": DEFAULT_MODEL,
        "template_version": TEMPLATE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mini_report": pipeline["mini_report"],
    }

    # Render YAML by hand to avoid a yaml dep at runtime.
    def _quote(s: Any) -> str:
        """Always double-quote string values so YAML loaders don't auto-cast dates/bools."""
        return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'

    def _yaml_dump(d: dict[str, Any], indent: int = 0) -> str:
        lines: list[str] = []
        pad = "  " * indent
        for k, v in d.items():
            # Skip None entirely so jsonschema doesn't reject null-typed Score etc.
            if v is None:
                continue
            if isinstance(v, dict):
                lines.append(pad + str(k) + ":")
                lines.append(_yaml_dump(v, indent + 1))
            elif isinstance(v, list):
                if not v:
                    lines.append(pad + str(k) + ": []")
                else:
                    lines.append(pad + str(k) + ":")
                    for item in v:
                        if isinstance(item, dict):
                            lines.append(pad + "  -")
                            lines.append(_yaml_dump(item, indent + 2))
                        else:
                            lines.append(pad + "  - " + _quote(item))
            elif isinstance(v, bool):
                lines.append(pad + str(k) + ": " + str(v).lower())
            elif isinstance(v, (int, float)):
                lines.append(pad + str(k) + ": " + str(v))
            else:
                # Always quote strings - protects dates, empty strings, special chars, etc.
                lines.append(pad + str(k) + ": " + _quote(v))
        return "\n".join(lines)

    yaml_block = _yaml_dump(frontmatter)
    md = "---\n" + yaml_block + "\n---\n\n# " + title + "\n\n" + pipeline["mini_report"]["topic_sentence"] + "\n\n"
    for b in pipeline["mini_report"]["bullets"]:
        md += "- " + b + "\n"
    md += "\n---\n\n**Source:** " + frontmatter["sources"][0] + "\n**Generated by:** `" + frontmatter["prompt_version"] + "` on `" + frontmatter["model"] + "`\n"

    if dry_run:
        print(md)
        return None

    CONTENT_REPORTS.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Only process cleaned files where the embedded date matches YYYY-MM-DD")
    parser.add_argument("--file", help="Process a specific cleaned/ file")
    parser.add_argument("--dry-run", action="store_true", help="Print report, don't write")
    parser.add_argument("--force", action="store_true", help="Re-summarize even if content/reports/ output exists")
    args = parser.parse_args()

    if not CLEANED.exists():
        print("ERROR: " + str(CLEANED) + " does not exist. Run `python scripts/clean.py` first.", file=sys.stderr)
        return 1

    if args.file:
        paths = [pathlib.Path(args.file)]
    else:
        paths = sorted(p for p in CLEANED.glob("*.md") if p.name.lower() != "readme.md")
        if args.date:
            paths = [p for p in paths if p.name.startswith(args.date)]

    written = 0
    skipped = 0
    for p in paths:
        out = summarize_one(p, dry_run=args.dry_run, force=args.force)
        if out:
            print("  -> " + str(out.relative_to(REPO_ROOT)), file=sys.stderr)
            written += 1
        else:
            skipped += 1

    print("Processed " + str(len(paths)) + " cleaned files - " + str(written) + " written, " + str(skipped) + " skipped.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
