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
from app.services.sheet_reader import sheet_reader
from app.services.date_parser import parse_brazilian_date_time
from app.core.websocket_manager import broadcast
import logging

logger = logging.getLogger(__name__)

FALLBACK_MESSAGE = "Aguarde um momento. Uma atendente vai te responder em breve. 😊"

async def process_incoming_message(from_number: str, body: str, to_number: str):
    db: Session = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(
            Tenant.whatsapp_number == to_number.replace("whatsapp:", "").replace("+", "").strip()
        ).first()

        if not tenant:
            print("❌ Tenant não encontrado")
            return

        # ====================== VERIFICA MODO HUMANO POR PACIENTE ======================
        status = db.query(ConversationStatus).filter(
            ConversationStatus.tenant_id == tenant.id,
            ConversationStatus.patient_phone == from_number,
            ConversationStatus.human_mode_active == True
        ).first()

        if status and status.human_mode_until and datetime.utcnow() < status.human_mode_until:
            print(f"👩‍💼 MODO HUMANO ATIVO para {from_number} → Bot NÃO responde mais")
            # Ainda salva a mensagem do paciente (para histórico e dashboard)
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
            return   # <--- BOT PARA AQUI

        print(f"🤖 Processando mensagem normal do paciente {from_number}")

        # ====================== SALVA + BROADCAST ======================
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
        db.refresh(log_in)

        await broadcast({
            "type": "new_message",
            "from": "paciente",
            "to": from_number,
            "message": body,
            "is_bot": False,
            "direction": "in",
            "timestamp": log_in.created_at.isoformat()
        })

        # ====================== PLANO BASIC ======================
        if tenant.plan == "basic":
            print("✅ PLANO BASIC ATIVADO → chamando basic_bot.py")
            response_text = await handle_basic_plan(body, from_number, tenant)

        # ====================== PLANO PREMIUM ======================
        else:
            print("🔴 PLANO PREMIUM → IA + Agendamento")
            response_text = None

            quick = get_quick_response(body, tenant.name or "clínica")
            if quick:
                response_text = quick
            elif any(p in body.lower() for p in ["agendar", "marcar", "consulta", "avaliação", "horário"]):
                response_text = "Entendi que quer agendar! Qual dia e horário você prefere?"
            else:
                try:
                    response_text = await get_ai_response(body, tenant, from_number)
                except:
                    response_text = FALLBACK_MESSAGE

        # ====================== ENVIA RESPOSTA ======================
        provider = TwilioProvider()
        await provider.send_message(from_number, response_text or FALLBACK_MESSAGE)

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

        await broadcast({
            "type": "new_message",
            "from": "bot",
            "to": from_number,
            "message": response_text or FALLBACK_MESSAGE,
            "is_bot": True,
            "direction": "out",
            "timestamp": log_out.created_at.isoformat()
        })

        print(f"✅ Resposta enviada: {(response_text or FALLBACK_MESSAGE)[:150]}...")

    except Exception as e:
        logger.error(f"❌ Erro: {e}")
    finally:
        db.close()
        
        
        
