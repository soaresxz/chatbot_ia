"""
Endpoints de agendamentos.

GET    /appointments?filter=hoje|amanha|pendentes|todos&page=1
GET    /appointments/{id}
PATCH  /appointments/{id}/status
GET    /appointments/slots?date=YYYY-MM-DD
DELETE /appointments/{id}
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.plan_limits import has_feature
from app.schemas.appointment import AppointmentOut, AppointmentUpdate, AppointmentStatus, AvailableSlotsResponse
from app.services import appointment_service as svc

router = APIRouter(prefix="/appointments", tags=["appointments"])


# ─────────────────────────────────────────────────────────────────────────────
# Listar agendamentos
# ─────────────────────────────────────────────────────────────────────────────

@router.get("", summary="Lista agendamentos com filtro")
def list_appointments(
    filter: str = Query("todos", description="hoje | amanha | pendentes | todos"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = svc.list_appointments(
        db=db,
        tenant_id=current_user.tenant_id,
        filter=filter,
        page=page,
        page_size=page_size,
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Horários disponíveis
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/slots", response_model=AvailableSlotsResponse, summary="Retorna slots disponíveis para uma data")
def get_available_slots(
    date_str: str = Query(..., alias="date", description="Data no formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not has_feature(current_user.tenant.plan, "scheduling"):
        raise HTTPException(status_code=403, detail="Agendamentos disponíveis apenas nos planos Pro e Enterprise.")

    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=422, detail="Formato de data inválido. Use YYYY-MM-DD.")

    result = svc.get_available_slots(db, current_user.tenant_id, target_date)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Detalhe
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{appointment_id}", response_model=AppointmentOut, summary="Retorna um agendamento pelo ID")
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    appt = svc.get_appointment_by_id(db, appointment_id, current_user.tenant_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    return appt


# ─────────────────────────────────────────────────────────────────────────────
# Atualizar status
# ─────────────────────────────────────────────────────────────────────────────

@router.patch("/{appointment_id}/status", response_model=AppointmentOut, summary="Altera status do agendamento")
def update_appointment_status(
    appointment_id: int,
    body: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    appt = svc.get_appointment_by_id(db, appointment_id, current_user.tenant_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")

    if body.status == AppointmentStatus.CONFIRMADO:
        appt = svc.confirm_appointment(db, appointment_id, current_user.tenant_id)
    elif body.status == AppointmentStatus.CANCELADO:
        appt = svc.cancel_appointment(db, appointment_id, current_user.tenant_id)
    else:
        # Atualização genérica dos demais campos
        for field, value in body.dict(exclude_unset=True).items():
            setattr(appt, field, value)
        db.commit()
        db.refresh(appt)

    return appt


# ─────────────────────────────────────────────────────────────────────────────
# Excluir
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/{appointment_id}", summary="Remove um agendamento")
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    appt = svc.get_appointment_by_id(db, appointment_id, current_user.tenant_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    db.delete(appt)
    db.commit()
    return {"detail": "Agendamento removido com sucesso."}