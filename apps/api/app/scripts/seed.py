"""Seed the database with the 28 baseline industries.

Run: docker compose run --rm api python -m app.scripts.seed
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.db.models import Industry
from app.db.session import async_session

BASELINE = [
    ("banking", "Banking", "#6FC4E0"),
    ("real-estate", "Real Estate", "#E8B864"),
    ("technology", "Technology", "#9D7BE8"),
    ("energy", "Energy", "#F59E0B"),
    ("pharma", "Pharmaceutical", "#4ADE80"),
    ("automotive", "Automotive", "#F87171"),
    ("retail", "Retail", "#FB923C"),
    ("steel", "Steel", "#94A3B8"),
    ("securities", "Securities", "#2DD4BF"),
    ("manufacturing", "Manufacturing", "#A78BFA"),
    ("logistics", "Logistics", "#38BDF8"),
    ("agriculture", "Agriculture", "#84CC16"),
    ("construction", "Construction", "#FACC15"),
    ("utilities", "Utilities", "#60A5FA"),
    ("aviation", "Aviation", "#C084FC"),
    ("fnb", "F&B", "#F472B6"),
    ("insurance", "Insurance", "#22D3EE"),
    ("chemicals", "Chemicals", "#FB7185"),
    ("textiles", "Textiles", "#E879F9"),
    ("mining", "Mining", "#D4D4D8"),
    ("telecom", "Telecom", "#818CF8"),
    ("shipping", "Shipping", "#4FD1C5"),
    ("healthcare", "Healthcare", "#34D399"),
    ("education", "Education", "#FCD34D"),
    ("fisheries", "Fisheries", "#67E8F9"),
    ("industrial-parks", "Industrial Parks", "#FDE047"),
    ("consumer-goods", "Consumer Goods", "#F0ABFC"),
    ("other", "Other", "#A1A1AA"),
]


async def main() -> None:
    async with async_session() as db:
        existing = {r.slug for r in (await db.execute(select(Industry))).scalars().all()}
        added = 0
        for slug, name, color in BASELINE:
            if slug in existing:
                continue
            db.add(Industry(slug=slug, name=name, color=color))
            added += 1
        await db.commit()
        print(f"Seed complete: {added} new industries (of {len(BASELINE)} baseline).")


if __name__ == "__main__":
    asyncio.run(main())
