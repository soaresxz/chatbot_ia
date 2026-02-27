from app.core.database import SessionLocal
from app.models.tenant import Tenant
from app.models.message_log import MessageLog
from app.services.ai.gemini_agent import get_ai_response
from app.services.whatsapp.twilio_provider import TwilioProvider
from app.services.basic_bot import handle_basic_plan
import uuid
from datetime import datetime
from fastapi import WebSocket
import asyncio

# WebSocket connections ativas (para o Lovable receber atualizações em tempo real)
active_connections = set()

async def broadcast(message: dict):
    """Envia mensagem para todos os dashboards conectados no Lovable"""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            active_connections.discard(connection)

async def process_incoming_message(from_number: str, body: str, to_number: str):
    db = SessionLocal()
    tenant = db.query(Tenant).filter(
        Tenant.whatsapp_number == to_number.replace("whatsapp:", "").replace("+", "").strip()
    ).first()

    if not tenant:
        db.close()
        return

    # Verifica se o bot está pausado para esse cliente
    if tenant.human_mode_active or (tenant.human_mode_until and datetime.utcnow() < tenant.human_mode_until):
        db.close()
        return

    # Log da mensagem recebida
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

    # Roteamento por plano
    if tenant.plan == "basic":
        response_text = await handle_basic_plan(body, from_number, tenant)
    else:
        try:
            response_text = await get_ai_response(body, tenant, from_number)
        except Exception as e:
            print(f"❌ Erro na IA: {e}")
            response_text = "Aguarde um momento. Uma atendente vai te responder em breve."

    # Envia resposta
    if response_text:
        try:
            provider = TwilioProvider()
            sid = await provider.send_message(from_number, response_text)

            log_out = MessageLog(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                from_phone=to_number,
                to_phone=from_number,
                message=response_text,
                direction="out",
                created_at=datetime.utcnow()
            )
            db.add(log_out)
            db.commit()

        except Exception as e:
            print(f"❌ Erro ao enviar: {e}")

    db.close()