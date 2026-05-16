from fastapi import APIRouter, status

from app.core.deps import DB
from app.services import vault as vault_svc

router = APIRouter()


@router.get("/status")
async def vault_status(db: DB) -> dict:
    return await vault_svc.status(db)


@router.post("/reconcile", status_code=status.HTTP_202_ACCEPTED)
async def reconcile() -> dict:
    job_id = await vault_svc.trigger_reconcile()
    return {"job_id": job_id, "status": "queued"}


@router.post("/refresh", status_code=status.HTTP_202_ACCEPTED)
async def refresh() -> dict:
    job_id = await vault_svc.trigger_reconcile()
    return {"job_id": job_id, "status": "queued"}
