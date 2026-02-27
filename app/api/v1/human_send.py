from fastapi import APIRouter, Body
from app.services.whatsapp.twilio_provider import TwilioProvider
from app.services.whatsapp.service import broadcast
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/human-send")
async def human_send(
    phone: str = Body(...),
    message: str = Body(...)
):
    logger.info(f"[HUMANO SEND] Recebido → Phone: {phone} | Msg: {message[:100]}...")

    try:
        provider = TwilioProvider()

        # Limpeza rigorosa
        phone_clean = phone.replace("whatsapp:", "").replace(" ", "").strip()
        if not phone_clean.startswith("+"):
            phone_clean = "+" + phone_clean

        full_to = f"whatsapp:{phone_clean}"

        sid = await provider.send_message(full_to, message)

        logger.info(f"[HUMANO SEND] ✅ Enviado com sucesso! SID: {sid}")

        await broadcast({
            "type": "new_message",
            "from": "humano",
            "to": phone,
            "message": message,
            "is_bot": False,
            "sid": sid
        })

        return {"status": "success", "sid": sid}

    except Exception as e:
        logger.error(f"[HUMANO SEND] ERRO: {e}")
        return {"status": "error", "message": str(e)}