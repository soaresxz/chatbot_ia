from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from datetime import datetime, timedelta
from app.models.appointment import Appointment
from app.models.tenant import Tenant

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/clinica/{tenant_id}")
def get_clinica_report(tenant_id: str, db: Session = Depends(get_db)):
    hoje = datetime.utcnow().date()
    inicio_mes = hoje.replace(day=1)

    total_mes = db.scalar(
        select(func.count()).where(
            and_(
                Appointment.tenant_id == tenant_id,
                Appointment.scheduled_date >= inicio_mes
            )
        )
    ) or 0

    confirmados_mes = db.scalar(
        select(func.count()).where(
            and_(
                Appointment.tenant_id == tenant_id,
                Appointment.scheduled_date >= inicio_mes,
                Appointment.status == "confirmed"
            )
        )
    ) or 0

    faturamento_mes = db.scalar(
        select(func.sum(Appointment.value)).where(
            and_(
                Appointment.tenant_id == tenant_id,
                Appointment.scheduled_date >= inicio_mes
            )
        )
    ) or 0.0

    return {
        "periodo": f"{inicio_mes.strftime('%B %Y')}",
        "total_agendamentos": total_mes,
        "taxa_confirmacao": round((confirmados_mes / total_mes * 100), 1) if total_mes > 0 else 0.0,
        "faturamento_mes": round(float(faturamento_mes), 2),
        "grafico_diario": []  # vamos expandir depois
    }
    