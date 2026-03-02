from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.models.appointment import Appointment, AppointmentStatus

class DashboardService:
    @staticmethod
    async def get_clinica_dashboard(db: AsyncSession, tenant_id: str):
        hoje = datetime.utcnow().date()

        # === CÁLCULOS REAIS DO BANCO (sem números fictícios) ===
        total_hoje = await db.scalar(
            select(func.count())
            .where(
                and_(
                    Appointment.tenant_id == tenant_id,
                    func.date(Appointment.scheduled_date) == hoje
                )
            )
        ) or 0

        confirmados = await db.scalar(
            select(func.count())
            .where(
                and_(
                    Appointment.tenant_id == tenant_id,
                    func.date(Appointment.scheduled_date) == hoje,
                    Appointment.status == AppointmentStatus.CONFIRMED
                )
            )
        ) or 0

        faltas = await db.scalar(
            select(func.count())
            .where(
                and_(
                    Appointment.tenant_id == tenant_id,
                    func.date(Appointment.scheduled_date) == hoje,
                    Appointment.status == AppointmentStatus.NO_SHOW
                )
            )
        ) or 0

        faturamento = await db.scalar(
            select(func.sum(Appointment.value))
            .where(
                and_(
                    Appointment.tenant_id == tenant_id,
                    func.date(Appointment.scheduled_date) == hoje
                )
            )
        ) or 0.0

        taxa_confirmacao = round((confirmados / total_hoje * 100), 1) if total_hoje > 0 else 0.0

        return {
            "agendamentos_hoje": int(total_hoje),
            "confirmados": int(confirmados),
            "taxa_confirmacao": float(taxa_confirmacao),
            "faltas": int(faltas),
            "faturamento_projetado": round(float(faturamento), 2),
            "proximos_agendamentos": 0,      # vamos expandir na próxima etapa
            "mensagens_hoje": 0
        }