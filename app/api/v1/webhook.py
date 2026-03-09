import asyncio
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

        def normalize(n: str) -> str:
            return ''.join(filter(str.isdigit, n.replace("whatsapp:", "").replace("+", "")))

        tenant = db.query(Tenant).filter(
            Tenant.whatsapp_number.ilike(f"%{normalize(to_number)}%")
        ).first()

        if not tenant:
            return {"status": "ignored"}

        if normalize(from_number) == normalize(tenant.whatsapp_number):
            # ✅ Responde imediatamente e processa em background
            asyncio.create_task(handle_attendant_message(tenant, to_number))
            return {"status": "queued"}

        # ✅ Responde imediatamente ao Twilio/Meta e processa em background
        asyncio.create_task(process_incoming_message(tenant, from_number, body))
        return {"status": "queued"}

    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        return {"status": "error"}