from typing import Literal

from fastapi import APIRouter

from app.core.deps import DB
from app.services import industries as ind_svc

router = APIRouter()


@router.get("")
async def list_industries(db: DB) -> list[dict]:
    return await ind_svc.list_all(db)


@router.get("/heatmap")
async def heatmap(db: DB, window: Literal["1d", "7d", "30d"] = "1d") -> dict:
    return await ind_svc.heatmap(db, window=window)


@router.get("/{slug}")
async def get_industry(slug: str, db: DB) -> dict:
    return await ind_svc.get_by_slug(db, slug)
