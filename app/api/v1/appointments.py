from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.plan_limits import has_feature
from app.models.tenant import Tenant
from app.schemas.appointment import AppointmentOut, AppointmentUpdate, AppointmentStatus, AvailableSlotsResponse
from app.services import appointment_service as svc

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _get_tenant(db: Session, tenant_id: str) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Clínica não encontrada.")
    return tenant


@router.get("", summary="Lista agendamentos com filtro")
def list_appointments(
    filter: str = Query("todos", description="hoje | amanha | pendentes | todos"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return svc.list_appointments(db=db, tenant_id=current_user.tenant_id,
                                 filter=filter, page=page, page_size=page_size)


@router.get("/slots", response_model=AvailableSlotsResponse, summary="Slots disponíveis para uma data")
def get_available_slots(
    date_str: str = Query(..., alias="date", description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tenant = current_user.tenant
    if not has_feature(tenant.plan, "scheduling"):
        raise HTTPException(status_code=403, detail="Agendamentos disponíveis apenas nos planos Pro e Enterprise.")
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=422, detail="Formato de data inválido. Use YYYY-MM-DD.")
    return svc.get_available_slots(db, current_user.tenant_id, target_date)


@router.get("/{appointment_id}", response_model=AppointmentOut, summary="Retorna agendamento pelo ID")
def get_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    appt = svc.get_appointment_by_id(db, appointment_id, current_user.tenant_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    return appt


@router.patch("/{appointment_id}/status", response_model=AppointmentOut, summary="Altera status")
def update_appointment_status(
    appointment_id: str,
    body: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    appt = svc.get_appointment_by_id(db, appointment_id, current_user.tenant_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")

    if body.status == AppointmentStatus.CONFIRMED:
        appt = svc.confirm_appointment(db, appointment_id, current_user.tenant_id)
    elif body.status == AppointmentStatus.CANCELLED:
        appt = svc.cancel_appointment(db, appointment_id, current_user.tenant_id)
    else:
        for field, value in body.dict(exclude_unset=True).items():
            setattr(appt, field, value)
        db.commit()
        db.refresh(appt)
    return appt


@router.delete("/{appointment_id}", summary="Remove agendamento")
def delete_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    appt = svc.get_appointment_by_id(db, appointment_id, current_user.tenant_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")
    db.delete(appt)
    db.commit()
    return {"detail": "Agendamento removido com sucesso."}