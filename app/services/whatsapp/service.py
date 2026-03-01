import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.tenant import Tenant
from app.models.message_log import MessageLog
from app.models.conversation_status import ConversationStatus
from app.services.whatsapp.twilio_provider import TwilioProvider
from app.services.intent_matcher import get_quick_response
from app.services.basic_bot import handle_basic_plan
from app.services.ai.gemini_agent import get_ai_response
from app.core.websocket_manager import broadcast
import logging
import traceback

logger = logging.getLogger(__name__)

FALLBACK_MESSAGE = "Aguarde um momento. Uma atendente vai te responder em breve. 😊"

async def process_incoming_message(from_number: str, body: str, to_number: str):
    db: Session = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(
            Tenant.whatsapp_number.ilike(f"%{to_number.replace('whatsapp:', '').replace('+', '').strip()}%")
        ).first()

        if not tenant:
            print("❌ Tenant não encontrado")
            return

        # Modo humano
        status = db.query(ConversationStatus).filter(
            ConversationStatus.tenant_id == tenant.id,
            ConversationStatus.patient_phone == from_number,
            ConversationStatus.human_mode_active == True
        ).first()

        if status and status.human_mode_until and datetime.utcnow() < status.human_mode_until:
            print(f"👩‍💼 MODO HUMANO ATIVO para {from_number}")
            return

        print(f"🤖 Processando mensagem normal do paciente {from_number}")

        # Salva log entrada
        log_in = MessageLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            from_phone=from_number,
            to_phone=to_number,
            message=body,
            direction="in",
            created_at=datetime.utcnow()
        )
        db.add(log_in)
        db.commit()

        await broadcast({"type": "new_message", "from": "paciente", "message": body, "is_bot": False})

        # Gera resposta
        if tenant.plan == "basic":
            response_text = await handle_basic_plan(body, from_number, tenant)
        else:
            quick = get_quick_response(body, tenant.name or "clínica")
            if quick:
                response_text = quick
            else:
                response_text = await get_ai_response(body, tenant, from_number) or FALLBACK_MESSAGE

        # ================== ENVIO TWILIO COM DEBUG PESADO ==================
        print(f"📤 ENVIANDO PARA TWILIO → Para: {from_number} | Mensagem: {response_text[:120]}...")

        provider = TwilioProvider()
        try:
            message_sid = await provider.send_message(from_number, response_text or FALLBACK_MESSAGE)
            print(f"✅ TWILIO ACEITOU! SID: {message_sid}")
        except Exception as send_error:
            print(f"❌ FALHA NO TWILIO: {send_error}")
            traceback.print_exc()

        # Log saída
        log_out = MessageLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            from_phone=to_number,
            to_phone=from_number,
            message=response_text or FALLBACK_MESSAGE,
            direction="out",
            created_at=datetime.utcnow()
        )
        db.add(log_out)
        db.commit()

        await broadcast({"type": "new_message", "from": "bot", "message": response_text, "is_bot": True})

        print(f"✅ Processo finalizado - Resposta: {response_text[:150]}...")

    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        traceback.print_exc()
    finally:
        db.close()