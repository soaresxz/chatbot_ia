from sqlalchemy import select, func, and_, distinct
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.appointment import Appointment, AppointmentStatus
from app.models.message_log import MessageLog
from app.models.conversation_status import ConversationStatus


class DashboardService:
    @staticmethod
    def get_clinica_dashboard(db: Session, tenant_id: str):
        hoje = datetime.utcnow().date()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        inicio_mes = hoje.replace(day=1)
        inicio_hoje = datetime.combine(hoje, datetime.min.time())
        inicio_semana_dt = datetime.combine(inicio_semana, datetime.min.time())
        inicio_mes_dt = datetime.combine(inicio_mes, datetime.min.time())

        # ── Agendamentos ─────────────────────────────────────

        total_hoje = db.scalar(
            select(func.count()).where(
                and_(
                    Appointment.tenant_id == tenant_id,
                    func.date(Appointment.scheduled_date) == hoje,
                )
            )
        ) or 0

        confirmados = db.scalar(
            select(func.count()).where(
                and_(
                    Appointment.tenant_id == tenant_id,
                    func.date(Appointment.scheduled_date) == hoje,
                    Appointment.status == AppointmentStatus.CONFIRMED,
                )
            )
        ) or 0

        faltas = db.scalar(
            select(func.count()).where(
                and_(
                    Appointment.tenant_id == tenant_id,
                    func.date(Appointment.scheduled_date) == hoje,
                    Appointment.status == AppointmentStatus.CANCELLED,
                )
            )
        ) or 0

        proximos = db.scalar(
            select(func.count()).where(
                and_(
                    Appointment.tenant_id == tenant_id,
                    Appointment.scheduled_date > datetime.utcnow(),
                    Appointment.status == AppointmentStatus.CONFIRMED,
                )
            )
        ) or 0

        # ── Faturamento real ─────────────────────────────────

        faturamento_mes = db.scalar(
            select(func.coalesce(func.sum(Appointment.value), 0.0)).where(
                and_(
                    Appointment.tenant_id == tenant_id,
                    Appointment.scheduled_date >= inicio_mes_dt,
                    Appointment.status == AppointmentStatus.COMPLETED,
                )
            )
        ) or 0.0

        # ── Conversas (pacientes únicos) ──────────────────────

        conversas_hoje = db.scalar(
            select(func.count(distinct(MessageLog.from_phone))).where(
                and_(
                    MessageLog.tenant_id == tenant_id,
                    MessageLog.direction == "in",
                    MessageLog.created_at >= inicio_hoje,
                )
            )
        ) or 0

        conversas_semana = db.scalar(
            select(func.count(distinct(MessageLog.from_phone))).where(
                and_(
                    MessageLog.tenant_id == tenant_id,
                    MessageLog.direction == "in",
                    MessageLog.created_at >= inicio_semana_dt,
                )
            )
        ) or 0

        conversas_mes = db.scalar(
            select(func.count(distinct(MessageLog.from_phone))).where(
                and_(
                    MessageLog.tenant_id == tenant_id,
                    MessageLog.direction == "in",
                    MessageLog.created_at >= inicio_mes_dt,
                )
            )
        ) or 0

        # ── Taxa de conversão (pacientes únicos → agendamentos) ─

        pacientes_com_agendamento = db.scalar(
            select(func.count(distinct(Appointment.patient_id))).where(
                and_(
                    Appointment.tenant_id == tenant_id,
                    Appointment.created_at >= inicio_mes_dt,
                )
            )
        ) or 0

        taxa_conversao = (
            round(pacientes_com_agendamento / conversas_mes * 100, 1)
            if conversas_mes > 0
            else 0.0
        )

        # ── Modo humano vs IA ─────────────────────────────────

        total_status = db.query(ConversationStatus).filter(
            ConversationStatus.tenant_id == tenant_id
        ).all()

        em_humano = sum(1 for s in total_status if s.human_mode_active)
        em_ia = len(total_status) - em_humano

        # ── Tempo médio de resposta do bot (em segundos) ──────
        # Estratégia: para cada mensagem "in", busca a próxima "out" mais próxima
        # Usa uma subquery para pegar pares in→out do mesmo tenant

        tempo_medio_resposta = DashboardService._calc_avg_response_time(
            db, tenant_id, inicio_hoje
        )

        # ── Taxa de confirmação de agendamentos ──────────────

        taxa_confirmacao = (
            round(confirmados / total_hoje * 100, 1) if total_hoje > 0 else 0.0
        )

        return {
            # Agendamentos
            "agendamentos_hoje": int(total_hoje),
            "confirmados": int(confirmados),
            "faltas": int(faltas),
            "proximos_agendamentos": int(proximos),
            "taxa_confirmacao": float(taxa_confirmacao),
            "faturamento_mes": round(float(faturamento_mes), 2),

            # Conversas
            "conversas_hoje": int(conversas_hoje),
            "conversas_semana": int(conversas_semana),
            "conversas_mes": int(conversas_mes),
            "taxa_conversao": float(taxa_conversao),

            # Atendimento
            "conversas_humano": int(em_humano),
            "conversas_ia": int(em_ia),
            "tempo_medio_resposta_segundos": tempo_medio_resposta,

            # Legado (mantido para compatibilidade com frontend atual)
            "faturamento_projetado": round(float(faturamento_mes), 2),
            "mensagens_hoje": int(conversas_hoje),
        }

    @staticmethod
    def _calc_avg_response_time(db: Session, tenant_id: str, desde: datetime) -> float:
        """
        Calcula o tempo médio de resposta do bot hoje.
        Para cada mensagem recebida (in), busca a resposta enviada (out) mais próxima.
        Retorna a média em segundos, ou 0.0 se não houver dados.
        """
        msgs_in = (
            db.query(MessageLog)
            .filter(
                MessageLog.tenant_id == tenant_id,
                MessageLog.direction == "in",
                MessageLog.created_at >= desde,
            )
            .order_by(MessageLog.created_at)
            .all()
        )

        if not msgs_in:
            return 0.0

        msgs_out = (
            db.query(MessageLog)
            .filter(
                MessageLog.tenant_id == tenant_id,
                MessageLog.direction == "out",
                MessageLog.created_at >= desde,
            )
            .order_by(MessageLog.created_at)
            .all()
        )

        if not msgs_out:
            return 0.0

        deltas = []
        for msg_in in msgs_in:
            # Primeira resposta após esta mensagem
            resposta = next(
                (m for m in msgs_out if m.created_at > msg_in.created_at), None
            )
            if resposta:
                delta = (resposta.created_at - msg_in.created_at).total_seconds()
                if delta < 300:  # ignora pares com mais de 5min (provavelmente não relacionados)
                    deltas.append(delta)

        return round(sum(deltas) / len(deltas), 1) if deltas else 0.0