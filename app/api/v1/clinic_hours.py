"""
Endpoints de configuração de horários da clínica.

GET    /clinic-hours              → lista todos os dias configurados
PUT    /clinic-hours/{day}        → cria ou atualiza configuração para o dia (0–6)
DELETE /clinic-hours/{day}        → remove configuração do dia (fecha a clínica naquele dia)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from sqlalchemy.orm import Session
from app.models.clinic_hours import ClinicHours, DAY_NAMES
from app.schemas.clinic_hours import ClinicHoursCreate, ClinicHoursOut, ClinicHoursUpdate

router = APIRouter(prefix="/clinic-hours", tags=["clinic-hours"])


@router.get("", response_model=list[ClinicHoursOut], summary="Lista horários configurados")
def list_clinic_hours(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = db.execute(
        select(ClinicHours)
        .where(ClinicHours.tenant_id == current_user.tenant_id)
        .order_by(ClinicHours.day_of_week)
    )
    hours = result.scalars().all()
    out = []
    for h in hours:
        d = ClinicHoursOut.from_orm(h)
        d.day_name = DAY_NAMES.get(h.day_of_week, "")
        out.append(d)
    return out


@router.put("/{day_of_week}", response_model=ClinicHoursOut, summary="Cria ou atualiza configuração do dia")
def upsert_clinic_hours(
    day_of_week: int,
    body: ClinicHoursCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if day_of_week not in range(7):
        raise HTTPException(status_code=422, detail="day_of_week deve estar entre 0 e 6.")

    result = db.execute(
        select(ClinicHours).where(
            and_(
                ClinicHours.tenant_id == current_user.tenant_id,
                ClinicHours.day_of_week == day_of_week,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.start_time = body.start_time
        existing.end_time = body.end_time
        existing.slot_duration_minutes = body.slot_duration_minutes
        existing.is_active = body.is_active
        db.commit()
        db.refresh(existing)
        ch = existing
    else:
        ch = ClinicHours(
            tenant_id=current_user.tenant_id,
            day_of_week=day_of_week,
            start_time=body.start_time,
            end_time=body.end_time,
            slot_duration_minutes=body.slot_duration_minutes,
            is_active=body.is_active,
        )
        db.add(ch)
        db.commit()
        db.refresh(ch)

    out = ClinicHoursOut.from_orm(ch)
    out.day_name = DAY_NAMES.get(ch.day_of_week, "")
    return out


@router.delete("/{day_of_week}", summary="Remove configuração do dia (clínica fechada)")
def delete_clinic_hours(
    day_of_week: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = db.execute(
        select(ClinicHours).where(
            and_(
                ClinicHours.tenant_id == current_user.tenant_id,
                ClinicHours.day_of_week == day_of_week,
            )
        )
    )
    ch = result.scalar_one_or_none()
    if not ch:
        raise HTTPException(status_code=404, detail="Configuração não encontrada para este dia.")
    db.delete(ch)
    db.commit()
    return {"detail": f"Configuração de {DAY_NAMES.get(day_of_week, '')} removida."}