from fastapi import APIRouter

from app.core.deps import DB
from app.schemas.search import SearchIn, SearchOut
from app.services import search as search_svc

router = APIRouter()


@router.post("", response_model=SearchOut)
async def search_endpoint(body: SearchIn, db: DB) -> SearchOut:
    return await search_svc.search(db, body)
