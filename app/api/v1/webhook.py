import asyncio
from functools import partial
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.services.whatsapp.service import process_incoming_message
from app.core.database import get_db, SessionLocal
from app.models.tenant import Tenant

router = APIRouter()


def normalize(n: str) -> str:
    return ''.join(filter(str.isdigit, n.replace("whatsapp:", "").replace("+", "")))


def _run_process(tenant_id: str, patient_phone: str, message_text: str):
    print(f"🔄 _run_process iniciado: tenant={tenant_id} phone={patient_phone} msg={message_text[:30]}")
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        print(f"🏥 Tenant encontrado: {tenant}")
        if tenant:
            process_incoming_message(db, tenant_id, tenant, patient_phone, message_text)
            print(f"✅ process_incoming_message concluído")
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


@router.post("/twilio/webhook")
async def twilio_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        form = await request.form()

        from_number = form.get("From", "").strip()
        to_number   = form.get("To", "").strip()
        body        = form.get("Body", "").strip()

        tenant = db.query(Tenant).filter(
            Tenant.whatsapp_number.ilike(f"%{normalize(to_number)}%")
        ).first()

        if not tenant:
            return {"status": "ignored"}

        if normalize(from_number) == normalize(tenant.whatsapp_number):
            return {"status": "ignored"}

        loop = asyncio.get_event_loop()
        loop.run_in_executor(
            None,
            partial(_run_process, tenant.id, from_number, body)
        )

        return {"status": "queued"}

    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error"}