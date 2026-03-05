"""
Webhook para WhatsApp Business Cloud API (Meta).

Endpoints:
  GET  /meta/webhook  → verificação do webhook pela Meta
  POST /meta/webhook  → recebimento de mensagens
"""
import asyncio
import os
import hmac
import hashlib
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.whatsapp.service import process_incoming_message
from app.models.tenant import Tenant

router = APIRouter()

META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "")
META_APP_SECRET = os.getenv("META_APP_SECRET", "")


def verify_meta_signature(payload: bytes, signature: str) -> bool:
    """Verifica assinatura HMAC-SHA256 da Meta para segurança."""
    if not META_APP_SECRET:
        return True  # em dev, pular verificação
    expected = "sha256=" + hmac.new(
        META_APP_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.get("/meta/webhook")
async def meta_webhook_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Verificação do webhook pela Meta.
    A Meta envia um GET com hub.challenge e espera o valor de volta.
    """
    if hub_mode == "subscribe" and hub_verify_token == META_VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(403, "Token de verificação inválido")


@router.post("/meta/webhook")
async def meta_webhook_receive(
    request: Request,
    db: Session = Depends(get_db),
):
    """Recebe mensagens do WhatsApp Cloud API."""
    try:
        # Verifica assinatura
        body_bytes = await request.body()
        signature = request.headers.get("x-hub-signature-256", "")
        if META_APP_SECRET and not verify_meta_signature(body_bytes, signature):
            raise HTTPException(401, "Assinatura inválida")

        data = await request.json()

        # Estrutura do payload da Meta
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                metadata = value.get("metadata", {})

                # Número do WhatsApp Business (To)
                display_phone = metadata.get("display_phone_number", "")
                to_number = f"+{display_phone}" if not display_phone.startswith("+") else display_phone

                for msg in messages:
                    if msg.get("type") != "text":
                        continue  # ignora áudio, imagem, etc. por enquanto

                    from_number = f"+{msg['from']}"
                    body = msg.get("text", {}).get("body", "").strip()

                    if not body:
                        continue

                    # Roteia para o tenant correto pelo número de destino
                    tenant = db.query(Tenant).filter(
                        Tenant.whatsapp_number.ilike(f"%{display_phone}%")
                    ).first()

                    if not tenant:
                        print(f"⚠️ Nenhum tenant para número Meta: {display_phone}")
                        continue

                    # ✅ Responde imediatamente e processa em background
                    asyncio.create_task(
                        process_incoming_message(from_number, body, to_number)
                    )

        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro no webhook Meta: {e}")
        return {"status": "error"}