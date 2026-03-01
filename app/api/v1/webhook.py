from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.services.whatsapp.service import process_incoming_message
from app.services.whatsapp.human_handler import handle_attendant_message
from app.core.database import get_db
from app.models.tenant import Tenant

router = APIRouter()

@router.post("/twilio/webhook")
async def twilio_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        
        from_number = form.get("From", "").strip()
        to_number   = form.get("To", "").strip()
        body        = form.get("Body", "").strip()

        print(f"\n📨 [WEBHOOK] Recebido → From: {from_number} | To: {to_number} | Msg: '{body}'")

        # Normalização do número
        def normalize(n):
            return ''.join(filter(str.isdigit, n.replace("whatsapp:", "").replace("+", "")))

        to_clean = normalize(to_number)

        # Busca tenant
        tenant = db.query(Tenant).filter(
            Tenant.whatsapp_number.ilike(f"%{to_clean}%")
        ).first()

        print("📋 Tenants cadastrados:")
        for t in db.query(Tenant).all():
            print(f"   → ID: {t.id} | WhatsApp: {t.whatsapp_number}")

        if not tenant:
            print(f"❌ Nenhum tenant encontrado para {to_clean}")
            return {"status": "ignored"}

        print(f"✅ Tenant encontrado: {tenant.id} - {getattr(tenant, 'name', 'Sem nome')}")

        # Modo humano (atendente)
        if normalize(from_number) == normalize(tenant.whatsapp_number):
            print("👤 Mensagem da atendente → Modo humano")
            handle_attendant_message(tenant, to_number)
            return {"status": "human_takeover"}

        # Mensagem do paciente
        print("💬 Processando mensagem do paciente...")
        await process_incoming_message(from_number, body, to_number)   # ← AQUI ESTAVA O ERRO (faltava await)
        print("✅ Processamento concluído com sucesso!")

        return {"status": "processed"}

    except Exception as e:
        print(f"❌ ERRO CRÍTICO NO WEBHOOK: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error"}