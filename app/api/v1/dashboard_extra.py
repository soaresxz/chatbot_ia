from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/clinica/{tenant_id}")
async def get_clinica_dashboard(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role == "clinic_user" and current_user.tenant_id != tenant_id:
        raise HTTPException(403, "Acesso negado")

    from app.services.dashboard_service import DashboardService
    try:
        metrics = await DashboardService.get_clinica_dashboard(db, tenant_id)
        return {"metrics": metrics, "tenant_id": tenant_id}
    except Exception as e:
        print(f"❌ ERRO DASHBOARD: {str(e)}")
        return {"error": str(e)}


@router.get("/conversations")
def get_dashboard_conversations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.models.message_log import MessageLog

    tenant_id = current_user.tenant_id or "sandbox_twilio"
    messages = (
        db.query(MessageLog)
        .filter(MessageLog.tenant_id == tenant_id)
        .order_by(MessageLog.created_at.desc())
        .limit(30)
        .all()
    )
    return {
        "conversas": [
            {
                "id": str(m.id),
                "paciente": "Cliente WhatsApp",
                "telefone": m.from_phone or "",
                "mensagem": m.message,
                "data": m.created_at.strftime("%d/%m %H:%M"),
                "direcao": "recebida" if m.direction == "in" else "enviada",
                "nao_lidas": 0,
            }
            for m in messages
        ]
    }