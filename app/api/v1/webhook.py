from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.services.whatsapp.service import process_incoming_message
from app.services.whatsapp.human_handler import handle_attendant_message
from app.core.database import get_db
from app.models.tenant import Tenant

import logging
import traceback

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/twilio/webhook")
async def twilio_webhook(
    request: Request,
    db: Session = Depends(get_db)   # ← agora síncrono
):
    try:
        form = await request.form()
        
        from_number = form.get("From", "").strip()
        to_number   = form.get("To", "").strip()
        body        = form.get("Body", "").strip()

        print(f"\n📨 [WEBHOOK] Recebido → From: {from_number} | To: {to_number} | Msg: '{body}'")

        # Busca tenant
        tenant = db.query(Tenant).filter(
            Tenant.whatsapp_number == to_number.replace("whatsapp:", "").replace("+", "").strip()
        ).first()

        if not tenant:
            print(f"⚠️  Tenant NÃO encontrado para número: {to_number}")
            return {"status": "ignored"}

        print(f"✅ Tenant encontrado: {tenant.name if hasattr(tenant, 'name') else 'sem nome'}")

        # Verifica se é mensagem da atendente (modo humano)
        attendant_clean = tenant.whatsapp_number.replace("whatsapp:", "").replace("+", "").strip()
        from_clean = from_number.replace("whatsapp:", "").replace("+", "").strip()

        if from_clean == attendant_clean:
            print(f"👤 MENSAGEM DA ATENDENTE → Modo humano ativado")
            handle_attendant_message(tenant, to_number)
            return {"status": "human_takeover"}

        # Mensagem normal do paciente
        print(f"💬 Processando mensagem do PACIENTE...")
        process_incoming_message(from_number, body, to_number, db)   # passa o db
        print(f"✅ Processamento concluído com sucesso!")

        return {"status": "processed"}

    except Exception as e:
        print(f"❌ ERRO CRÍTICO NO WEBHOOK: {e}")
        traceback.print_exc()
        return {"status": "error"}