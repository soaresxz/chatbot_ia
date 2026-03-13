"""
Ferramentas de agendamento para o Gemini Agent (function calling).

Cada função é declarada como tool para o Gemini e tem uma implementação
assíncrona que executa a lógica no banco de dados.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import appointment_service as svc

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Declarações de ferramentas (formato Gemini function_declarations)
# ─────────────────────────────────────────────────────────────────────────────

APPOINTMENT_TOOLS = [
    {
        "name": "verificar_disponibilidade",
        "description": (
            "Verifica os horários disponíveis para agendamento em uma data específica. "
            "Use quando o paciente perguntar quando pode marcar ou pedir sugestão de horário."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "Data no formato YYYY-MM-DD (ex: 2025-07-15)",
                }
            },
            "required": ["data"],
        },
    },
    {
        "name": "criar_agendamento",
        "description": (
            "Cria um agendamento com status PENDENTE e aguarda confirmação do paciente. "
            "Use somente depois de o paciente ter escolhido data e horário."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "data_hora": {
                    "type": "string",
                    "description": "Data e hora no formato YYYY-MM-DD HH:MM (ex: 2025-07-15 14:30)",
                },
                "procedimento": {
                    "type": "string",
                    "description": "Nome do procedimento odontológico (ex: Limpeza, Extração, Clareamento)",
                },
                "nome_paciente": {
                    "type": "string",
                    "description": "Nome do paciente para registro",
                },
            },
            "required": ["data_hora"],
        },
    },
    {
        "name": "listar_agendamentos_paciente",
        "description": (
            "Lista os agendamentos futuros do paciente pelo número de telefone. "
            "Use quando o paciente perguntar sobre seus agendamentos ou quiser remarcar."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "telefone": {
                    "type": "string",
                    "description": "Número de telefone do paciente no formato internacional",
                }
            },
            "required": ["telefone"],
        },
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Implementações das ferramentas
# ─────────────────────────────────────────────────────────────────────────────

async def execute_tool(
    tool_name: str,
    args: dict[str, Any],
    db: AsyncSession,
    tenant_id: int,
    patient_phone: str,
) -> str:
    """
    Executa a ferramenta solicitada pelo Gemini e retorna uma string descritiva
    que será adicionada ao contexto para a próxima resposta do modelo.
    """
    try:
        if tool_name == "verificar_disponibilidade":
            return await _verificar_disponibilidade(args, db, tenant_id)
        elif tool_name == "criar_agendamento":
            return await _criar_agendamento(args, db, tenant_id, patient_phone)
        elif tool_name == "listar_agendamentos_paciente":
            return await _listar_agendamentos_paciente(args, db, tenant_id, patient_phone)
        else:
            return f"Ferramenta '{tool_name}' não reconhecida."
    except Exception as e:
        logger.error(f"Erro ao executar tool {tool_name}: {e}", exc_info=True)
        return f"Erro interno ao executar a função {tool_name}."


async def _verificar_disponibilidade(args: dict, db: AsyncSession, tenant_id: int) -> str:
    data_str = args.get("data", "")
    try:
        target_date = date.fromisoformat(data_str)
    except ValueError:
        return "Data inválida. Use o formato YYYY-MM-DD."

    result = svc.get_available_slots(db, tenant_id, target_date)

    if not result["slots"]:
        msg = result.get("message", "Não há horários disponíveis nesta data.")
        return f"[{result['day_name']} {data_str}] {msg}"

    slots_fmt = ", ".join(result["slots"])
    return (
        f"Horários disponíveis para {result['day_name']}, {data_str}: {slots_fmt}. "
        f"Total: {len(result['slots'])} horários livres."
    )


async def _criar_agendamento(
    args: dict, db: AsyncSession, tenant_id: int, patient_phone: str
) -> str:
    data_hora_str = args.get("data_hora", "")
    try:
        scheduled_dt = datetime.strptime(data_hora_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return "Data/hora inválida. Use o formato YYYY-MM-DD HH:MM."

    # Verifica se o slot ainda está disponível
    slots_info = svc.get_available_slots(db, tenant_id, scheduled_dt.date())
    slot_str = scheduled_dt.strftime("%H:%M")
    if slot_str not in slots_info.get("slots", []):
        return (
            f"O horário {slot_str} de {data_hora_str[:10]} não está disponível. "
            f"Horários livres: {', '.join(slots_info.get('slots', [])[:5])}."
        )

    from app.schemas.appointment import AppointmentCreate

    appt_data = AppointmentCreate(
        patient_phone=patient_phone,
        patient_name=args.get("nome_paciente"),
        procedure=args.get("procedimento"),
        scheduled_date=scheduled_dt,
    )
    appt = svc.create_appointment(db, tenant_id, appt_data)

    return (
        f"AGENDAMENTO_PENDENTE|id={appt.id}|"
        f"data={scheduled_dt.strftime('%d/%m/%Y')}|"
        f"hora={slot_str}|"
        f"procedimento={args.get('procedimento', 'Consulta')}"
    )


async def _listar_agendamentos_paciente(
    args: dict, db: AsyncSession, tenant_id: int, patient_phone: str
) -> str:
    from sqlalchemy import select, and_
    from app.models.appointment import Appointment
    from app.schemas.appointment import AppointmentStatus

    now = datetime.utcnow()
    result = db.execute(
        select(Appointment).where(
            and_(
                Appointment.tenant_id == tenant_id,
                Appointment.patient_phone == patient_phone,
                Appointment.scheduled_date >= now,
                Appointment.status.in_([AppointmentStatus.PENDENTE, AppointmentStatus.CONFIRMADO]),
            )
        ).order_by(Appointment.scheduled_date.asc()).limit(5)
    )
    appointments = result.scalars().all()

    if not appointments:
        return "Nenhum agendamento futuro encontrado para este paciente."

    lines = []
    for a in appointments:
        lines.append(
            f"- {a.scheduled_date.strftime('%d/%m/%Y %H:%M')} | "
            f"{a.procedure or 'Consulta'} | Status: {a.status}"
        )
    return "Agendamentos futuros:\n" + "\n".join(lines)