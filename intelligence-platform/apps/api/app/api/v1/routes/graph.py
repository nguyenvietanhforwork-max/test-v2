"""Knowledge graph slice — entity neighborhood for the dashboard graph view."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models.news import NewsItem
from app.models.wiki import Entity, NewsItemEntity

router = APIRouter()


@router.get("")
async def graph_slice(
    session: Annotated[AsyncSession, Depends(get_session)],
    entity: str | None = None,
    depth: int = 1,
) -> dict:
    """Returns nodes + edges for a force-directed layout."""
    if not entity:
        # return top 50 entities by news mention count
        rows = await session.execute(
            select(Entity).limit(50)
        )
        entities = rows.scalars().all()
        return {"nodes": [_e(e) for e in entities], "edges": []}

    # naive depth-1
    root = await session.scalar(select(Entity).where(Entity.name == entity))
    if not root:
        return {"nodes": [], "edges": []}

    news_rows = await session.execute(
        select(NewsItem)
        .join(NewsItemEntity, NewsItemEntity.news_item_id == NewsItem.id)
        .where(NewsItemEntity.entity_id == root.id)
        .limit(50)
    )
    news_items = news_rows.scalars().all()

    co_entities_rows = await session.execute(
        select(Entity)
        .join(NewsItemEntity, NewsItemEntity.entity_id == Entity.id)
        .where(
            NewsItemEntity.news_item_id.in_([n.id for n in news_items]),
            Entity.id != root.id,
        )
        .limit(100)
    )
    co_entities = co_entities_rows.scalars().unique().all()

    nodes = [_e(root)] + [_e(e) for e in co_entities]
    edges = [{"from": str(root.id), "to": str(e.id)} for e in co_entities]
    return {"nodes": nodes, "edges": edges}


def _e(e: Entity) -> dict:
    return {"id": str(e.id), "name": e.name, "type": e.type.value, "ticker": e.ticker}
