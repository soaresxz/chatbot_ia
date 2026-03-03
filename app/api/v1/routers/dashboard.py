"""
Paths gerados (sem prefixo adicional no include_router):
  GET /dashboard/clinica/{tenant_id}
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/clinica/{tenant_id}")
def get_clinica_dashboard(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role == "clinic_user" and current_user.tenant_id != tenant_id:
        raise HTTPException(403, "Acesso negado")

    try:
        metrics = DashboardService.get_clinica_dashboard(db, tenant_id)
        return {"metrics": metrics, "tenant_id": tenant_id}
    except Exception as e:
        print(f"❌ ERRO DASHBOARD: {str(e)}")
        return {"error": str(e)}