import asyncio
from functools import partial
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.services.whatsapp.service import process_incoming_message
from app.services.whatsapp.human_handler import handle_attendant_message
from app.core.database import get_db, SessionLocal
from app.models.tenant import Tenant

router = APIRouter()


def normalize(n: str) -> str:
    return ''.join(filter(str.isdigit, n.replace("whatsapp:", "").replace("+", "")))


def _run_process(tenant_id: str, tenant, patient_phone: str, message_text: str):
    """Executa em thread separada com sua própria sessão de DB."""
    db = SessionLocal()
    try:
        process_incoming_message(db, tenant_id, tenant, patient_phone, message_text)
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

        # Roda a função síncrona em thread pool sem bloquear o event loop
        loop = asyncio.get_event_loop()
        loop.run_in_executor(
            None,
            partial(_run_process, tenant.id, tenant, from_number, body)
        )

        return {"status": "queued"}

    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        return {"status": "error"}