import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.tenant import Tenant
from app.models.message_log import MessageLog
from app.models.conversation_status import ConversationStatus
from app.services.whatsapp.provider_factory import get_provider
from app.services.intent_matcher import get_quick_response
from app.services.basic_bot import handle_basic_plan
from app.services.ai.gemini_agent import get_ai_response
from app.core.websocket_manager import broadcast
from app.core.plan_limits import check_plan_limit, LIMIT_REACHED_MESSAGE

FALLBACK_MESSAGE = "Aguarde um momento. Uma atendente vai te responder em breve. 😊"


def normalize_phone(phone: str) -> str:
    """Remove 'whatsapp:' e garante '+' no início."""
    clean = phone.replace("whatsapp:", "").replace(" ", "").strip()
    if clean and not clean.startswith("+"):
        clean = "+" + clean
    return clean


async def process_incoming_message(from_number: str, body: str, to_number: str):
    db: Session = SessionLocal()
    try:
        from_clean = normalize_phone(from_number)
        to_clean = normalize_phone(to_number)

        tenant = db.query(Tenant).filter(
            Tenant.whatsapp_number.ilike(f"%{to_clean.replace('+', '')}%")
        ).first()

        if not tenant:
            print(f"⚠️ Nenhum tenant encontrado para o número: {to_number}")
            return

        # Verifica se modo humano está ativo para este paciente
        status = db.query(ConversationStatus).filter(
            ConversationStatus.tenant_id == tenant.id,
            ConversationStatus.patient_phone == from_clean,
            ConversationStatus.human_mode_active == True
        ).first()

        human_mode = False
        if status:
            if status.human_mode_until is None or datetime.utcnow() < status.human_mode_until:
                human_mode = True
                print(f"🙋 Modo humano ativo para {from_clean}, bot pausado.")

        # ✅ Sempre salva a mensagem recebida e faz broadcast — independente do modo
        now_in = datetime.utcnow()
        log_in = MessageLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            from_phone=from_clean,   # ✅ normalizado
            to_phone=to_clean,       # ✅ normalizado
            message=body,
            direction="in",
            created_at=now_in
        )
        db.add(log_in)
        db.commit()

        await broadcast({
            "type": "new_message",
            "tenant_id": tenant.id,
            "patient_phone": from_clean,
            "message": {
                "id": log_in.id,
                "content": body,
                "direction": "in",
                "timestamp": now_in.isoformat(),
                "sender_name": None,
            }
        })

        # ✅ Se modo humano, para aqui — mensagem já foi salva e transmitida
        if human_mode:
            return

        # ✅ Verifica limite do plano antes de responder
        allowed, reason = check_plan_limit(db, tenant)
        if not allowed:
            print(f"🚫 Limite de plano atingido para {tenant.id}: {reason}")
            provider = TwilioProvider()
            await provider.send_message(f"whatsapp:{from_clean}", LIMIT_REACHED_MESSAGE)
            return

        # Gera resposta conforme plano
        if tenant.plan == "basic":
            response_text = await handle_basic_plan(body, from_clean, tenant)
        else:
            quick = get_quick_response(body, tenant.name or "clínica")
            response_text = quick or await get_ai_response(body, tenant, from_clean) or FALLBACK_MESSAGE

        # Envia resposta
        provider = get_provider(tenant)
        await provider.send_message(f"whatsapp:{from_clean}", response_text)

        now_out = datetime.utcnow()
        log_out = MessageLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            from_phone=to_clean,     # ✅ número da clínica normalizado
            to_phone=from_clean,     # ✅ número do paciente normalizado
            message=response_text,
            direction="out",
            created_at=now_out
        )
        db.add(log_out)
        db.commit()

        await broadcast({
            "type": "new_message",
            "tenant_id": tenant.id,
            "patient_phone": from_clean,
            "message": {
                "id": log_out.id,
                "content": response_text,
                "direction": "out",
                "timestamp": now_out.isoformat(),
                "sender_name": "Bot",
            }
        })

        print(f"✅ Resposta enviada para {from_clean}")

    finally:
        db.close()