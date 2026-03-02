from sqlalchemy import func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from app.models.appointment import Appointment, AppointmentStatus
from app.models.tenant import Tenant

class DashboardService:
    @staticmethod
    async def get_clinica_dashboard(db: AsyncSession, tenant_id: str):
        hoje = datetime.utcnow().date()
        inicio_mes = hoje.replace(day=1)

        # Contagens reais
        total_hoje = await db.scalar(
            func.count().select().where(
                and_(Appointment.tenant_id == tenant_id, func.date(Appointment.scheduled_date) == hoje)
            )
        )

        confirmados = await db.scalar(
            func.count().select().where(
                and_(Appointment.tenant_id == tenant_id, 
                     func.date(Appointment.scheduled_date) == hoje,
                     Appointment.status == AppointmentStatus.CONFIRMED)
            )
        )

        faltas = await db.scalar(
            func.count().select().where(
                and_(Appointment.tenant_id == tenant_id, 
                     func.date(Appointment.scheduled_date) == hoje,
                     Appointment.status == AppointmentStatus.NO_SHOW)
            )
        )

        faturamento = await db.scalar(
            func.sum(Appointment.value).select().where(
                and_(Appointment.tenant_id == tenant_id, func.date(Appointment.scheduled_date) == hoje)
            )
        ) or 0.0

        taxa = round((confirmados / total_hoje * 100) if total_hoje > 0 else 0, 1)

        return {
            "agendamentos_hoje": total_hoje or 0,
            "confirmados": confirmados or 0,
            "taxa_confirmacao": taxa,
            "faltas": faltas or 0,
            "faturamento_projetado": round(float(faturamento), 2),
            "proximos_agendamentos": 0,  # podemos expandir depois
            "mensagens_hoje": 0           # vamos adicionar depois
        }