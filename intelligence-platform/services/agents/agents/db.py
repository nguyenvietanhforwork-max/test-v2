"""Thin async DB layer for the agents service. Mirrors a subset of the API's models.

Intentionally schema-light: agents do not own migrations. The API owns the
authoritative ORM; agents access via plain SQL to avoid model duplication.
"""

from datetime import date as date_
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from agents.config import settings

engine = create_async_engine(settings.database_url, pool_size=5, max_overflow=10)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def fetch_news_item(news_item_id: str):
    async with Session() as s:
        row = (
            await s.execute(
                text("select id, raw_text, language, title, source_url from news_items where id = :id"),
                {"id": news_item_id},
            )
        ).mappings().one()
        return type("NewsRow", (), dict(row))


async def upsert_classification(
    *,
    news_item_id: str,
    bucket: str,
    industries: list[str],
    countries: list[str],
    companies: list[str],
    confidence: float,
    model: str,
    prompt_version: str,
) -> None:
    async with Session() as s:
        await s.execute(
            text(
                """
                insert into classifications
                  (news_item_id, bucket, industries, countries, companies, confidence, model, prompt_version)
                values (:nid, :bucket, :industries, :countries, :companies, :conf, :model, :pv)
                on conflict (news_item_id) do update
                  set bucket = excluded.bucket,
                      industries = excluded.industries,
                      countries = excluded.countries,
                      companies = excluded.companies,
                      confidence = excluded.confidence,
                      model = excluded.model,
                      prompt_version = excluded.prompt_version,
                      updated_at = now()
                """
            ),
            {
                "nid": news_item_id,
                "bucket": bucket,
                "industries": industries,
                "countries": countries,
                "companies": companies,
                "conf": confidence,
                "model": model,
                "pv": prompt_version,
            },
        )
        await s.execute(
            text("update news_items set status='classified' where id = :id"),
            {"id": news_item_id},
        )
        await s.commit()


async def upsert_summary(
    *,
    news_item_id: str,
    thesis: str,
    supporting_points: list[dict],
    implications: list[dict],
    data_points: list[dict],
    model: str,
    prompt_version: str,
) -> None:
    import json

    async with Session() as s:
        await s.execute(
            text(
                """
                insert into summaries
                  (news_item_id, thesis, supporting_points, implications, data_points, model, prompt_version)
                values (:nid, :thesis, :sup::jsonb, :imp::jsonb, :dp::jsonb, :model, :pv)
                on conflict (news_item_id) do update
                  set thesis = excluded.thesis,
                      supporting_points = excluded.supporting_points,
                      implications = excluded.implications,
                      data_points = excluded.data_points,
                      model = excluded.model,
                      prompt_version = excluded.prompt_version,
                      updated_at = now()
                """
            ),
            {
                "nid": news_item_id,
                "thesis": thesis,
                "sup": json.dumps(supporting_points),
                "imp": json.dumps(implications),
                "dp": json.dumps(data_points),
                "model": model,
                "pv": prompt_version,
            },
        )
        await s.execute(
            text("update news_items set status='summarized' where id = :id"),
            {"id": news_item_id},
        )
        await s.commit()


async def list_entities_for_news_item(news_item_id: str) -> list[Any]:
    async with Session() as s:
        rows = (await s.execute(
            text("""
                select e.* from entities e
                join news_item_entities n on n.entity_id = e.id
                where n.news_item_id = :id
            """),
            {"id": news_item_id},
        )).mappings().all()
        return [dict(r) for r in rows]


async def retrieve_wiki_context(query: str, k: int = 5) -> list[str]:
    # placeholder — caller can embed and query. Returns titles only for now.
    async with Session() as s:
        rows = (await s.execute(
            text("select body_md from wiki_pages where title ilike :q limit :k"),
            {"q": f"%{query}%", "k": k},
        )).scalars().all()
        return list(rows)


async def upsert_wiki_page(*, slug: str, title: str, body_md: str) -> None:
    async with Session() as s:
        await s.execute(
            text(
                """
                insert into wiki_pages (slug, title, type, body_md, vault_path)
                values (:slug, :title, 'entity', :body, :vault)
                on conflict (slug) do update
                  set body_md = excluded.body_md,
                      title = excluded.title,
                      updated_at = now()
                """
            ),
            {"slug": slug, "title": title, "body": body_md, "vault": f"wiki/{slug}.md"},
        )
        await s.commit()


async def link_wiki_to_news(*, slug: str, news_item_id: str) -> None:
    async with Session() as s:
        await s.execute(
            text(
                """
                insert into wiki_page_sources (wiki_page_id, news_item_id, citation_text)
                select wp.id, :nid, '' from wiki_pages wp where wp.slug = :slug
                on conflict do nothing
                """
            ),
            {"nid": news_item_id, "slug": slug},
        )
        await s.commit()


async def items_for_date(date_str: str) -> list:
    async with Session() as s:
        rows = (await s.execute(
            text("""
                select ni.id, ni.title, ni.source_url,
                       row_to_json(c.*) as classification,
                       row_to_json(sm.*) as summary
                  from news_items ni
                  left join classifications c on c.news_item_id = ni.id
                  left join summaries sm on sm.news_item_id = ni.id
                 where ni.publish_date = :d
                 order by ni.created_at desc
            """),
            {"d": date_str},
        )).mappings().all()
        return [type("Row", (), dict(r))() for r in rows]


async def save_report(*, date, type: str, body_md: str, model: str, prompt_version: str) -> str:
    async with Session() as s:
        row = (await s.execute(
            text(
                """
                insert into reports (date, type, body_md, model, prompt_version)
                values (:d, :t, :b, :m, :pv)
                returning id::text
                """
            ),
            {"d": date, "t": type, "b": body_md, "m": model, "pv": prompt_version},
        )).scalar_one()
        await s.commit()
        return row


async def update_report_pdf(*, report_id: str, pdf_url: str) -> None:
    async with Session() as s:
        await s.execute(
            text("update reports set pdf_url = :u, updated_at = now() where id = :id"),
            {"u": pdf_url, "id": report_id},
        )
        await s.commit()


async def mark_news_status(news_item_id: str, status: str) -> None:
    async with Session() as s:
        await s.execute(
            text("update news_items set status = :s where id = :id"),
            {"s": status, "id": news_item_id},
        )
        await s.commit()
