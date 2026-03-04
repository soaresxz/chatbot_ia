from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from collections import defaultdict
from typing import Optional

from app.core.database import get_db
from app.models.message_log import MessageLog
from app.models.tenant import Tenant
from app.models.conversation_status import ConversationStatus
from app.core.auth import get_current_user

router = APIRouter(prefix="/conversations")


def normalize_phone(phone: str) -> str:
    clean = phone.replace("whatsapp:", "").replace(" ", "").strip()
    if clean and not clean.startswith("+"):
        clean = "+" + clean
    return clean


def resolve_tenant_id(current_user, tenant_id_param: Optional[str]) -> str:
    if current_user.role == "clinic_user":
        if not current_user.tenant_id:
            raise HTTPException(403, "Usuário sem clínica associada")
        return current_user.tenant_id
    if not tenant_id_param:
        raise HTTPException(422, "tenant_id é obrigatório para administradores")
    return tenant_id_param


@router.get("")
def list_conversations(
    tenant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tid = resolve_tenant_id(current_user, tenant_id)

    tenant = db.query(Tenant).filter(Tenant.id == tid).first()
    if not tenant:
        return {"conversations": [], "total": 0}

    messages = (
        db.query(MessageLog)
        .filter(MessageLog.tenant_id == tid)
        .order_by(desc(MessageLog.created_at))
        .all()
    )

    # ✅ Carrega todos os ConversationStatus do tenant de uma vez (evita N+1 queries)
    statuses = {
        s.patient_phone: s
        for s in db.query(ConversationStatus).filter(
            ConversationStatus.tenant_id == tid
        ).all()
    }

    grouped = defaultdict(list)
    for msg in messages:
        # ✅ normaliza o phone para evitar chaves duplicadas (ex: "+55..." vs "whatsapp:+55...")
        raw = msg.from_phone if msg.direction == "in" else msg.to_phone
        phone = normalize_phone(raw) if raw else None
        if phone:
            grouped[phone].append(msg)

    result = []
    for phone, msgs in grouped.items():
        last = msgs[0]
        # ✅ Status individual por patient_phone, não do tenant inteiro
        conv_status = statuses.get(phone)
        is_human = conv_status.human_mode_active if conv_status else False

        result.append({
            "id": phone,
            "patient_name": f"Paciente {phone[-4:]}",
            "patient_phone": phone,
            "last_message": last.message or "",
            "last_message_time": last.created_at.isoformat(),
            "updated_at": last.created_at.isoformat(),
            "status": "human_mode" if is_human else "ai_mode",
            "unread_count": 0,
        })

    result.sort(key=lambda x: x["updated_at"], reverse=True)
    return {"conversations": result, "total": len(result)}


@router.get("/{patient_phone}")
def get_conversation(
    patient_phone: str,
    tenant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tid = resolve_tenant_id(current_user, tenant_id)

    messages = (
        db.query(MessageLog)
        .filter(
            MessageLog.tenant_id == tid,
            (MessageLog.from_phone == patient_phone) | (MessageLog.to_phone == patient_phone),
        )
        .order_by(MessageLog.created_at)
        .all()
    )

    return {
        "patient_phone": patient_phone,
        "messages": [
            {
                "id": str(m.id),
                "content": m.message or "",
                "direction": m.direction or "in",
                "timestamp": m.created_at.isoformat(),
                "sender_name": None,
            }
            for m in messages
        ],
    }