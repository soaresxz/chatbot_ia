"""
WhatsApp Service — Processa mensagens recebidas.

Fluxo de mensagem:
1. Verificar modo humano → se ativo, ignora IA
2. Verificar limite de plano → se excedido, notifica e para
3. Verificar confirmação pendente (SIM/NÃO) → confirma/cancela agendamento
4. Enviar para Gemini → obter resposta
5. Se Gemini retornou agendamento pendente → salvar na conversa e pedir confirmação
6. Enviar resposta ao paciente
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plan_limits import check_plan_limit, PLAN_SCHEDULING
from app.models.conversation_status import ConversationStatus
from app.services import appointment_service as appt_svc
from app.services.ai.gemini_agent import generate_response
from app.services.whatsapp.provider_factory import get_whatsapp_provider

logger = logging.getLogger(__name__)

# Palavras reconhecidas como confirmação / cancelamento
_YES_WORDS = {"sim", "s", "confirmar", "confirmo", "ok", "yes"}
_NO_WORDS = {"nao", "não", "n", "cancelar", "cancelo", "no"}


async def process_incoming_message(
    db: AsyncSession,
    tenant_id: int,
    tenant: object,
    patient_phone: str,
    message_text: str,
) -> None:
    """Ponto central de processamento de mensagens recebidas."""

    # ── 1. Modo humano ──────────────────────────────────────────────────────
    conv_status = await _get_or_create_conversation(db, tenant_id, patient_phone)

    if conv_status.human_mode_active:
        if conv_status.human_mode_until and conv_status.human_mode_until < datetime.utcnow():
            # Expirou → sai do modo humano
            conv_status.human_mode_active = False
            conv_status.pending_confirmation = None
            await db.commit()
        else:
            logger.info(f"[tenant={tenant_id}] Modo humano ativo para {patient_phone} — mensagem ignorada pela IA")
            return

    # ── 2. Limite de plano ──────────────────────────────────────────────────
    allowed, msg_limit = await check_plan_limit(db, tenant_id, tenant.plan)
    if not allowed:
        provider = get_whatsapp_provider(tenant)
        await provider.send_message(
            to=patient_phone,
            message="Desculpe, nossa clínica atingiu o limite mensal de mensagens. Entre em contato diretamente.",
        )
        return

    # ── 3. Confirmação pendente (SIM / NÃO) ────────────────────────────────
    if conv_status.pending_confirmation:
        handled = await _handle_confirmation(
            db, tenant, tenant_id, patient_phone, message_text, conv_status
        )
        if handled:
            return

    # ── 4. Gemini ───────────────────────────────────────────────────────────
    has_scheduling = PLAN_SCHEDULING.get(tenant.plan, False)

    # Monta contexto do tenant para o agente
    tenant_context = f"{getattr(tenant, 'name', '')} | {getattr(tenant, 'dentist_name', '')}"

    history = _build_history(conv_status)

    response_text, pending_info = await generate_response(
        message=message_text,
        history=history,
        db=db,
        tenant_id=tenant_id,
        patient_phone=patient_phone,
        has_scheduling=has_scheduling,
        tenant_context=tenant_context,
    )

    # ── 5. Salva agendamento pendente na conversa ───────────────────────────
    if pending_info:
        conv_status.pending_confirmation = pending_info
        await db.commit()

    # ── 6. Envia resposta ───────────────────────────────────────────────────
    provider = get_whatsapp_provider(tenant)
    await provider.send_message(to=patient_phone, message=response_text)

    # Salva no histórico de mensagens (message_log)
    await _log_messages(db, tenant_id, patient_phone, tenant.whatsapp_number, message_text, response_text)


# ─────────────────────────────────────────────────────────────────────────────
# Confirmação SIM / NÃO
# ─────────────────────────────────────────────────────────────────────────────

async def _handle_confirmation(
    db: AsyncSession,
    tenant,
    tenant_id: int,
    patient_phone: str,
    message_text: str,
    conv_status: ConversationStatus,
) -> bool:
    """
    Verifica se a mensagem é uma resposta SIM/NÃO para agendamento pendente.
    Retorna True se a mensagem foi tratada aqui (não precisa ir para a IA).
    """
    normalized = _normalize(message_text)
    pending = conv_status.pending_confirmation  # dict: {id, data, hora, procedimento}

    provider = get_whatsapp_provider(tenant)

    if normalized in _YES_WORDS:
        appt_id = int(pending.get("id", 0))
        appt = await appt_svc.confirm_appointment(db, appt_id, tenant_id)
        conv_status.pending_confirmation = None
        await db.commit()

        if appt:
            reply = (
                f"✅ Agendamento confirmado!\n"
                f"📅 {pending.get('data', '')} às {pending.get('hora', '')}\n"
                f"🦷 {pending.get('procedimento', 'Consulta')}\n\n"
                f"Te esperamos! Em caso de imprevisto, entre em contato para reagendar."
            )
        else:
            reply = "Não encontrei o agendamento para confirmar. Por favor, refaça o agendamento."

        await provider.send_message(to=patient_phone, message=reply)
        return True

    if normalized in _NO_WORDS:
        appt_id = int(pending.get("id", 0))
        await appt_svc.cancel_appointment(db, appt_id, tenant_id)
        conv_status.pending_confirmation = None
        await db.commit()

        reply = (
            "Agendamento cancelado. Se quiser marcar em outro horário, é só me dizer! 😊"
        )
        await provider.send_message(to=patient_phone, message=reply)
        return True

    # Mensagem ambígua → volta para IA, mas mantém pending para próxima tentativa
    return False


def _normalize(text: str) -> str:
    """Remove acentos, lowercase e espaços extras."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", text.strip().lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _get_or_create_conversation(
    db: AsyncSession, tenant_id: int, patient_phone: str
) -> ConversationStatus:
    from sqlalchemy import select, and_
    result = await db.execute(
        select(ConversationStatus).where(
            and_(
                ConversationStatus.tenant_id == tenant_id,
                ConversationStatus.patient_phone == patient_phone,
            )
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        conv = ConversationStatus(
            tenant_id=tenant_id,
            patient_phone=patient_phone,
            human_mode_active=False,
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
    return conv


def _build_history(conv_status: ConversationStatus) -> list[dict]:
    """Reconstrói histórico da conversa a partir do message_log armazenado."""
    if not hasattr(conv_status, "message_log") or not conv_status.message_log:
        return []
    return conv_status.message_log  # já deve estar no formato [{role, content}]


async def _log_messages(
    db: AsyncSession,
    tenant_id: int,
    patient_phone: str,
    clinic_number: str,
    user_message: str,
    bot_reply: str,
) -> None:
    """Salva mensagem do paciente e resposta do bot na tabela message_log."""
    from app.models.message_log import MessageLog  # ajuste conforme seu modelo
    now = datetime.utcnow()
    db.add_all([
        MessageLog(
            tenant_id=tenant_id,
            from_phone=patient_phone,
            to_phone=clinic_number,
            message=user_message,
            direction="inbound",
            created_at=now,
        ),
        MessageLog(
            tenant_id=tenant_id,
            from_phone=clinic_number,
            to_phone=patient_phone,
            message=bot_reply,
            direction="outbound",
            created_at=now,
        ),
    ])
    await db.commit()