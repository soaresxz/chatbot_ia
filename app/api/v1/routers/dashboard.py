from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/clinica/{tenant_id}")
async def get_clinica_dashboard(tenant_id: str, db: AsyncSession = Depends(get_db)):
    metrics = await DashboardService.get_clinica_dashboard(db, tenant_id)
    return {"metrics": metrics}