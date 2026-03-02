from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from collections import defaultdict
from app.core.database import get_db
from app.models.message_log import MessageLog
from app.models.tenant import Tenant

router = APIRouter(prefix="/conversations")

@router.get("")
def list_conversations(tenant_id: str = Query(...), db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return {"conversations": []}

    messages = db.query(MessageLog).filter(
        MessageLog.tenant_id == tenant_id
    ).order_by(desc(MessageLog.created_at)).all()

    grouped = defaultdict(list)
    for msg in messages:
        phone = msg.from_phone if msg.direction == "in" else msg.to_phone
        if phone:
            grouped[phone].append(msg)

    result = []
    for phone, msgs in grouped.items():
        last = msgs[0]
        result.append({
            "id": phone,
            "patient_name": f"Paciente {phone[-4:]}",
            "patient_phone": phone,
            "last_message": last.message or "",
            "last_message_time": last.created_at.isoformat(),
            "updated_at": last.created_at.isoformat(),
            "status": "human_mode" if getattr(tenant, "human_mode_active", False) else "ai_mode",
            "unread_count": 0,
        })

    # Ordena por mais recente
    result.sort(key=lambda x: x["updated_at"], reverse=True)

    return {"conversations": result, "total": len(result)}


@router.get("/{patient_phone}")
def get_conversation(patient_phone: str, tenant_id: str = Query(...), db: Session = Depends(get_db)):
    messages = db.query(MessageLog).filter(
        MessageLog.tenant_id == tenant_id,
        (MessageLog.from_phone == patient_phone) | (MessageLog.to_phone == patient_phone)
    ).order_by(MessageLog.created_at).all()

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
        ]
    }