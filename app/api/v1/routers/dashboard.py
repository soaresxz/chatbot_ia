from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/clinica/{tenant_id}")
def get_clinica_dashboard(tenant_id: str, db: Session = Depends(get_db)):
    metrics = DashboardService.get_clinica_dashboard(db, tenant_id)
    return {"metrics": metrics, "tenant_id": tenant_id}