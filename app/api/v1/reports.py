from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.tenant import Tenant
from app.models.message_log import MessageLog
from datetime import datetime, timedelta

router = APIRouter(prefix="/reports")

@router.get("/admin")
def admin_reports(db: Session = Depends(get_db)):
    return {
        "total_clinicas": db.query(Tenant).count(),
        "mensagens_hoje": 0,  # pode melhorar depois
        "agendamentos_hoje": 0
    }

@router.get("/clinic")
def clinic_reports(tenant_id: str = Query(...), db: Session = Depends(get_db)):
    return {
        "mensagens_hoje": 0,
        "agendamentos_hoje": 0,
        "pacientes_ativos": 0
    }