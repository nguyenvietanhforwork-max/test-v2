"""Hybrid search: pgvector cosine + Meilisearch lexical, RRF re-ranked."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.schemas.news import SearchHit, SearchRequest
from app.services.search import hybrid_search

router = APIRouter()


@router.post("", response_model=list[SearchHit])
async def search(
    body: SearchRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[SearchHit]:
    return await hybrid_search(session, body.q, body.filters, body.k)
