from fastapi import APIRouter, HTTPException, status

from app.core.deps import DB
from app.services import entities as entities_svc

router = APIRouter()


@router.get("/{slug}")
async def get_entity(slug: str, db: DB) -> dict:
    e = await entities_svc.get_by_slug(db, slug)
    if not e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "entity not found")
    return e


@router.get("/{slug}/timeline")
async def entity_timeline(slug: str, db: DB, limit: int = 50) -> dict:
    return {"items": await entities_svc.timeline(db, slug, limit=limit)}
