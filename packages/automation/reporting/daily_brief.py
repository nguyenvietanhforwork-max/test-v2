"""Build the daily intelligence brief — markdown + PDF.

Run at 06:00 ICT by Celery Beat. Also callable on-demand.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import httpx
import redis.asyncio as redis_asyncio
from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from app.core.config import settings  # type: ignore[import-not-found]
from app.db.models import (  # type: ignore[import-not-found]
    NewsEntity,
    NewsIndustry,
    NewsItem,
    Report,
    ReportSection,
    ReportSource,
    ReportType,
)
from app.db.session import async_session  # type: ignore[import-not-found]
from packages.agents.models import get_chat

THESIS_PROMPT = (Path(__file__).parents[2] / "agents" / "prompts" / "thesis_generator.txt").read_text(encoding="utf-8")


async def build_today() -> dict:
    return await build_for(date.today())


async def build_for(target: date) -> dict:
    async with async_session() as db:
        start = datetime.combine(target, datetime.min.time())
        end = start + timedelta(days=1)

        stmt = (
            select(NewsItem)
            .options(
                selectinload(NewsItem.industries).selectinload(NewsIndustry.industry),
                selectinload(NewsItem.entities).selectinload(NewsEntity.entity),
            )
            .where(NewsItem.published_at >= start)
            .where(NewsItem.published_at < end)
            .order_by(desc(NewsItem.published_at))
        )
        items = (await db.execute(stmt)).scalars().all()

        if not items:
            return {"status": "no-items", "date": target.isoformat()}

        # Thesis
        items_payload = [
            {
                "id": str(i.id),
                "thesis": i.thesis,
                "bullets": i.bullets,
                "region": i.region.value,
                "bucket": i.bucket.value,
                "industries": [ni.industry.slug for ni in i.industries],
                "entities": [ne.entity.name for ne in i.entities],
                "sentiment": i.sentiment,
            }
            for i in items
        ]
        chat = get_chat(settings.DEFAULT_MODEL)
        res = await chat.chat(system=THESIS_PROMPT, user=json.dumps(items_payload, ensure_ascii=False), max_tokens=800, temperature=0.4)
        thesis_doc = json.loads(res["text"])

        # Sections grouped by (region, bucket, industry)
        sections: list[dict] = _group_into_sections(items)
        markdown = _render_markdown(target, thesis_doc, sections)

        # Persist
        report = Report(
            id=uuid4(),
            type=ReportType.DAILY,
            title=f"Daily Intelligence Brief · {target.isoformat()}",
            thesis=thesis_doc["thesis"],
            markdown=markdown,
            published_at=datetime.utcnow(),
            period_start=start,
            period_end=end,
            version=1,
            meta={
                "subtitle": thesis_doc.get("subtitle", ""),
                "today_lead_industry": thesis_doc.get("today_lead_industry"),
                "todays_three_signals": thesis_doc.get("todays_three_signals", []),
                "stats": _compute_stats(items),
            },
        )
        db.add(report)
        await db.flush()

        for pos, sec in enumerate(sections):
            section = ReportSection(id=uuid4(), report_id=report.id, position=pos, heading=sec["heading"], body_md=sec["body_md"])
            db.add(section)
            await db.flush()
            for src in sec["sources"]:
                db.add(ReportSource(id=uuid4(), section_id=section.id, news_id=src["id"], citation_label=src.get("label")))

        # Write markdown to vault
        md_path = settings.VAULT_PROCESSED / "Report of news" / f"{target.isoformat()}.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")

        # PDF via microservice
        pdf_url = await _render_pdf(markdown, target)
        report.pdf_object_key = pdf_url

        # Move processed clippings into raw/old news/<date>/
        old_dir = settings.VAULT_RAW / "old news" / target.isoformat()
        old_dir.mkdir(parents=True, exist_ok=True)
        for i in items:
            try:
                src = Path(i.raw_path)
                if src.exists():
                    src.rename(old_dir / src.name)
            except Exception:
                pass

        await db.commit()

        # Broadcast
        rc = redis_asyncio.from_url(settings.REDIS_URL, decode_responses=True)
        await rc.publish("events:global", json.dumps({"type": "report.published", "payload": {"id": str(report.id), "type": "daily", "title": report.title}}))
        await rc.aclose()

        return {"status": "ok", "report_id": str(report.id), "items": len(items), "sections": len(sections)}


def _group_into_sections(items: list[NewsItem]) -> list[dict]:
    groups: dict[str, list[NewsItem]] = {}
    for i in items:
        bucket_label = "Macro" if i.bucket.value == "macro" else "Corporate"
        region_label = "Vietnam" if i.region.value == "VN" else "International"
        key = f"{region_label} {bucket_label}"
        groups.setdefault(key, []).append(i)

    sections = []
    for heading, group in groups.items():
        body_lines = []
        sources = []
        for it in group:
            body_lines.append(f"### {it.thesis}")
            for b in (it.bullets or []):
                body_lines.append(f"- {b}")
            tickers = ", ".join({(ne.entity.ticker or ne.entity.name) for ne in it.entities})
            body_lines.append(f"\n*Source*: [{it.source_name}]({it.url or ''}) · *Entities*: {tickers}\n")
            sources.append({"id": it.id, "label": it.source_name})
        sections.append({"heading": heading, "body_md": "\n".join(body_lines), "sources": sources})
    return sections


def _compute_stats(items: list[NewsItem]) -> list[dict]:
    sectors = {ni.industry.slug for i in items for ni in i.industries}
    avg_sentiment = sum((i.sentiment or 0) for i in items) / max(1, len(items))
    return [
        {"label": "Items Today", "value": str(len(items))},
        {"label": "Active Industries", "value": f"{len(sectors)}/28"},
        {"label": "Sentiment Index", "value": f"{avg_sentiment:+.2f}", "deltaTone": "pos" if avg_sentiment > 0 else "neg"},
        {"label": "Pipeline P95", "value": "—"},
    ]


def _render_markdown(target: date, thesis_doc: dict, sections: list[dict]) -> str:
    out = [
        f"# Daily Intelligence Brief · {target.isoformat()}",
        "",
        f"> **Thesis.** {thesis_doc['thesis']}",
        "",
        thesis_doc.get("subtitle", ""),
        "",
        "## Today's three signals",
        "",
    ]
    for s in thesis_doc.get("todays_three_signals", []):
        out.append(f"- {s}")
    out.append("")
    for sec in sections:
        out.append(f"## {sec['heading']}")
        out.append("")
        out.append(sec["body_md"])
        out.append("")
    return "\n".join(out)


async def _render_pdf(markdown: str, target: date) -> str:
    async with httpx.AsyncClient(base_url=settings.PDF_SERVICE_URL, timeout=120.0) as c:
        res = await c.post("/render", json={"markdown": markdown, "filename": f"daily-{target.isoformat()}.pdf"})
        res.raise_for_status()
        return res.json()["object_key"]
