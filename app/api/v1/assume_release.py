"""
Paths (com prefix="/api/v1" no include_router):
  POST /api/v1/conversations/assume   → JWT
  POST /api/v1/conversations/release  → JWT (corrigido — antes usava api_key)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversas - atendimento"])


class ConversationBody(BaseModel):
    patient_phone: str


def normalize_phone(phone: str) -> str:
    clean = phone.replace("whatsapp:", "").replace(" ", "").strip()
    if clean and not clean.startswith("+"):
        clean = "+" + clean
    return clean


@router.post("/assume")
async def assume_conversation(
    body: ConversationBody,
    tenant_id: str = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "clinic_user" and current_user.tenant_id != tenant_id:
        raise HTTPException(403, "Acesso negado")

    phone = normalize_phone(body.patient_phone)

    from app.models.conversation_status import ConversationStatus

    status = (
        db.query(ConversationStatus)
        .filter(
            ConversationStatus.tenant_id == tenant_id,
            ConversationStatus.patient_phone == phone,
        )
        .first()
    )
    if status:
        status.human_mode_active = True
        status.human_mode_until = None
    else:
        status = ConversationStatus(
            tenant_id=tenant_id,
            patient_phone=phone,
            human_mode_active=True,
            human_mode_until=None,
        )
        db.add(status)

    db.commit()

    # Notifica o dashboard sobre mudança de status
    from app.core.websocket_manager import broadcast
    await broadcast({
        "type": "status_change",
        "tenant_id": tenant_id,
        "patient_phone": phone,
        "status": "human_mode",
    })

    return {"status": "success", "mode": "human_mode"}


@router.post("/release")
async def release_conversation(
    body: ConversationBody,
    tenant_id: str = Query(...),
    current_user=Depends(get_current_user),  # ✅ JWT em vez de api_key
    db: Session = Depends(get_db),
):
    if current_user.role == "clinic_user" and current_user.tenant_id != tenant_id:
        raise HTTPException(403, "Acesso negado")

    phone = normalize_phone(body.patient_phone)

    from app.models.conversation_status import ConversationStatus

    status = (
        db.query(ConversationStatus)
        .filter(
            ConversationStatus.tenant_id == tenant_id,
            ConversationStatus.patient_phone == phone,
        )
        .first()
    )
    if status:
        status.human_mode_active = False
        status.human_mode_until = None
        db.commit()

    # Notifica o dashboard sobre mudança de status
    from app.core.websocket_manager import broadcast
    await broadcast({
        "type": "status_change",
        "tenant_id": tenant_id,
        "patient_phone": phone,
        "status": "ai_mode",
    })

    return {"status": "success", "mode": "ai_mode"}