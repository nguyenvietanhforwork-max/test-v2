from typing import Literal

from fastapi import APIRouter

from app.core.deps import DB
from app.services import graph as graph_svc

router = APIRouter()


@router.get("")
async def get_graph(
    db: DB,
    center: str | None = None,
    depth: int = 2,
    window: Literal["24h", "7d", "30d", "all"] = "7d",
) -> dict:
    return await graph_svc.slice(db, center=center, depth=depth, window=window)
