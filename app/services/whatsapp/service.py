from __future__ import annotations

import logging
import asyncio
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.plan_limits import check_plan_limit, PLAN_SCHEDULING
from app.models.conversation_status import ConversationStatus
from app.services import appointment_service as appt_svc
from app.services.ai.gemini_agent import generate_response
from app.services.whatsapp.provider_factory import get_provider

logger = logging.getLogger(__name__)

_YES_WORDS = {"sim", "s", "confirmar", "confirmo", "ok", "yes"}
_NO_WORDS  = {"nao", "não", "n", "cancelar", "cancelo", "no"}


def process_incoming_message(
    db: Session,
    tenant_id: str,
    tenant,
    patient_phone: str,
    message_text: str,
) -> None:

    # ── 1. Modo humano ──────────────────────────────────────────────────────
    conv_status = _get_or_create_conversation(db, tenant_id, patient_phone)

    if conv_status.human_mode_active:
        if conv_status.human_mode_until and conv_status.human_mode_until < datetime.utcnow():
            conv_status.human_mode_active = False
            conv_status.pending_confirmation = None
            db.commit()
        else:
            logger.info(f"[tenant={tenant_id}] Modo humano ativo para {patient_phone} — ignorado pela IA")
            return

    # ── 2. Limite de plano ──────────────────────────────────────────────────
    allowed, _ = check_plan_limit(db, tenant_id, tenant.plan)
    if not allowed:
        provider = get_provider(tenant)
        asyncio.run(provider.send_message(
            to=patient_phone,
            body="Desculpe, nossa clínica atingiu o limite mensal de mensagens. Entre em contato diretamente.",
        ))
        return

    # ── 3. Confirmação pendente (SIM / NÃO) ────────────────────────────────
    if conv_status.pending_confirmation:
        handled = _handle_confirmation(db, tenant, tenant_id, patient_phone, message_text, conv_status)
        if handled:
            return

    # ── 4. Gemini ───────────────────────────────────────────────────────────
    has_scheduling = PLAN_SCHEDULING.get(tenant.plan, False)
    tenant_context = f"{getattr(tenant, 'name', '')} | {getattr(tenant, 'dentist_name', '')}"
    history = _build_history(conv_status)

    response_text, pending_info = asyncio.run(generate_response(
        message=message_text,
        history=history,
        db=db,
        tenant_id=tenant_id,
        patient_phone=patient_phone,
        has_scheduling=has_scheduling,
        tenant_context=tenant_context,
    ))

    # ── 5. Salva agendamento pendente ───────────────────────────────────────
    if pending_info:
        conv_status.pending_confirmation = pending_info
        db.commit()

    # ── 6. Envia resposta ───────────────────────────────────────────────────
    provider = get_provider(tenant)
    asyncio.run(provider.send_message(to=patient_phone, body=response_text))
    _log_messages(db, tenant_id, patient_phone, tenant.whatsapp_number, message_text, response_text)


# ── Confirmação SIM / NÃO ─────────────────────────────────────────────────────

def _handle_confirmation(
    db: Session,
    tenant,
    tenant_id: str,
    patient_phone: str,
    message_text: str,
    conv_status: ConversationStatus,
) -> bool:
    normalized = _normalize(message_text)
    pending    = conv_status.pending_confirmation
    provider   = get_provider(tenant)

    if normalized in _YES_WORDS:
        appt_id = pending.get("id", "")          # UUID string
        appt = appt_svc.confirm_appointment(db, appt_id, tenant_id)
        conv_status.pending_confirmation = None
        db.commit()

        reply = (
            f"✅ Agendamento confirmado!\n"
            f"📅 {pending.get('data', '')} às {pending.get('hora', '')}\n"
            f"🦷 {pending.get('procedimento', 'Consulta')}\n\n"
            f"Te esperamos! Em caso de imprevisto, entre em contato para reagendar."
        ) if appt else "Não encontrei o agendamento para confirmar. Por favor, refaça o agendamento."

        asyncio.run(provider.send_message(to=patient_phone, body=reply))
        return True

    if normalized in _NO_WORDS:
        appt_id = pending.get("id", "")          # UUID string
        appt_svc.cancel_appointment(db, appt_id, tenant_id)
        conv_status.pending_confirmation = None
        db.commit()

        asyncio.run(provider.send_message(
            to=patient_phone,
            body="Agendamento cancelado. Se quiser marcar em outro horário, é só me dizer! 😊",
        ))
        return True

    return False


def _normalize(text: str) -> str:
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", text.strip().lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_create_conversation(db: Session, tenant_id: str, patient_phone: str) -> ConversationStatus:
    conv = db.query(ConversationStatus).filter(
        ConversationStatus.tenant_id == tenant_id,
        ConversationStatus.patient_phone == patient_phone,
    ).first()

    if not conv:
        conv = ConversationStatus(
            tenant_id=tenant_id,
            patient_phone=patient_phone,
            human_mode_active=False,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return conv


def _build_history(conv_status: ConversationStatus) -> list[dict]:
    if not hasattr(conv_status, "message_log") or not conv_status.message_log:
        return []
    return conv_status.message_log


def _log_messages(
    db: Session,
    tenant_id: str,
    patient_phone: str,
    clinic_number: str,
    user_message: str,
    bot_reply: str,
) -> None:
    from app.models.message_log import MessageLog
    now = datetime.utcnow()
    db.add_all([
        MessageLog(tenant_id=tenant_id, from_phone=patient_phone, to_phone=clinic_number,
                   message=user_message, direction="in",  created_at=now),
        MessageLog(tenant_id=tenant_id, from_phone=clinic_number, to_phone=patient_phone,
                   message=bot_reply,   direction="out", created_at=now),
    ])
    db.commit()