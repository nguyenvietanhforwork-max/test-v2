from fastapi import APIRouter

from app.api.v1 import entities, graph, industries, news, reports, search, vault

api_router = APIRouter()
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(entities.router, prefix="/entities", tags=["entities"])
api_router.include_router(industries.router, prefix="/industries", tags=["industries"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])
api_router.include_router(vault.router, prefix="/vault", tags=["vault"])
