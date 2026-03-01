from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.models.message_log import MessageLog
from app.models.tenant import Tenant
from datetime import datetime, timedelta
from app.core.config import settings


router = APIRouter(prefix="/conversations")

@router.get("")
def list_conversations(tenant_id: str = Query(...), db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return {"conversations": []}

    messages = db.query(MessageLog).filter(
        MessageLog.tenant_id == tenant_id
    ).order_by(desc(MessageLog.created_at)).all()

    from collections import defaultdict
    grouped = defaultdict(list)
    for msg in messages:
        patient_phone = msg.from_phone if msg.direction == "in" else msg.to_phone
        grouped[patient_phone].append(msg)

    result = []
    for phone, msgs in grouped.items():
        last = msgs[0]
        result.append({
            "patient_phone": phone,
            "last_message": last.message,
            "last_message_time": last.created_at.isoformat(),
            "unread": 0,
            "human_mode": False
        })

    return {"conversations": result}

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
                "message": m.message,
                "direction": m.direction,
                "created_at": m.created_at.isoformat()
            } for m in messages
        ]
    }