from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.appointment import Appointment, AppointmentStatus

class DashboardService:
    @staticmethod
    def get_clinica_dashboard(db: Session, tenant_id: str):
        hoje = datetime.utcnow().date()

        # Agendamentos hoje
        total_hoje = db.scalar(
            select(func.count()).where(
                and_(
                    Appointment.tenant_id == tenant_id,
                    func.date(Appointment.scheduled_date) == hoje
                )
            )
        ) or 0

        # Confirmados
        confirmados = db.scalar(
            select(func.count()).where(
                and_(
                    Appointment.tenant_id == tenant_id,
                    func.date(Appointment.scheduled_date) == hoje,
                    Appointment.status == AppointmentStatus.CONFIRMED
                )
            )
        ) or 0

        # Faltas (usando CANCELLED por enquanto - NO_SHOW ainda não existe no banco)
        faltas = db.scalar(
            select(func.count()).where(
                and_(
                    Appointment.tenant_id == tenant_id,
                    func.date(Appointment.scheduled_date) == hoje,
                    Appointment.status == AppointmentStatus.CANCELLED
                )
            )
        ) or 0

        # Faturamento projetado
        faturamento = db.scalar(
            select(func.sum(Appointment.value)).where(
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
            "proximos_agendamentos": 0,
            "mensagens_hoje": 0
        }