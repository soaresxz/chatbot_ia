"""
Paths gerados (com prefix="/api/v1" no include_router):
  POST /api/v1/conversations/assume
  POST /api/v1/conversations/release
"""
import os
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversas - atendimento"])

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")


@router.post("/assume")
async def assume_conversation(
    request: Request,
    tenant_id: str = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "clinic_user" and current_user.tenant_id != tenant_id:
        raise HTTPException(403, "Acesso negado")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    patient_phone = body.get("patient_phone") or body.get("patientPhone")
    if not patient_phone:
        raise HTTPException(422, "patient_phone é obrigatório")

    from app.models.conversation_status import ConversationStatus

    status = (
        db.query(ConversationStatus)
        .filter(
            ConversationStatus.tenant_id == tenant_id,
            ConversationStatus.patient_phone == patient_phone,
        )
        .first()
    )
    if status:
        status.human_mode_active = True
        status.human_mode_until = None
    else:
        status = ConversationStatus(
            tenant_id=tenant_id,
            patient_phone=patient_phone,
            human_mode_active=True,
            human_mode_until=None,
        )
        db.add(status)

    db.commit()
    return {"status": "success", "mode": "human_mode"}


@router.post("/release")
async def release_conversation(
    request: Request,
    tenant_id: str = Query(...),
    api_key: str = Query(None, alias="api_key"),
    db: Session = Depends(get_db),
):
    # Mantido com api_key para compatibilidade com integrações existentes
    if api_key != ADMIN_API_KEY:
        raise HTTPException(403, "Chave inválida")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    patient_phone = body.get("patient_phone") or body.get("patientPhone")
    if not patient_phone:
        raise HTTPException(422, "patient_phone é obrigatório")

    from app.models.conversation_status import ConversationStatus

    status = (
        db.query(ConversationStatus)
        .filter(
            ConversationStatus.tenant_id == tenant_id,
            ConversationStatus.patient_phone == patient_phone,
        )
        .first()
    )
    if status:
        status.human_mode_active = False
        status.human_mode_until = None
        db.commit()

    return {"status": "success", "mode": "ai_mode"}