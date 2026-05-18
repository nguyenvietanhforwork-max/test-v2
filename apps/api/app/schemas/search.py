from typing import Literal

from pydantic import BaseModel


class SearchIn(BaseModel):
    query: str
    mode: Literal["lexical", "semantic", "hybrid"] = "hybrid"
    filters: dict | None = None
    limit: int = 20


class SearchHit(BaseModel):
    id: str
    title: str
    snippet: str
    score: float
    match_type: Literal["lex", "sem", "hybrid"]
    highlights: list[str] = []
    url: str | None = None


class SearchOut(BaseModel):
    hits: list[SearchHit]
    took_ms: int
