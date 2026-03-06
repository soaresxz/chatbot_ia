from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.clinic_hours import ClinicHours, DAY_NAMES
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.schemas.appointment import AppointmentCreate

logger = logging.getLogger(__name__)
TZ = ZoneInfo("America/Sao_Paulo")


# ── Disponibilidade ───────────────────────────────────────────────────────────

def get_clinic_hours_for_day(db: Session, tenant_id: str, day_of_week: int) -> Optional[ClinicHours]:
    return db.query(ClinicHours).filter(
        ClinicHours.tenant_id == tenant_id,
        ClinicHours.day_of_week == day_of_week,
        ClinicHours.is_active == True,
    ).first()


def _generate_slots(start: time, end: time, duration_minutes: int) -> list[str]:
    slots = []
    current = datetime.combine(date.today(), start)
    end_dt  = datetime.combine(date.today(), end)
    delta   = timedelta(minutes=duration_minutes)
    while current + delta <= end_dt:
        slots.append(current.strftime("%H:%M"))
        current += delta
    return slots


def get_available_slots(db: Session, tenant_id: str, target_date: date) -> dict:
    day_of_week = target_date.weekday()
    hours = get_clinic_hours_for_day(db, tenant_id, day_of_week)

    if not hours:
        return {
            "date": target_date.isoformat(),
            "day_name": DAY_NAMES.get(day_of_week, ""),
            "slots": [],
            "message": "Clínica não atende neste dia.",
        }

    all_slots = _generate_slots(hours.start_time, hours.end_time, hours.slot_duration_minutes)

    day_start = datetime.combine(target_date, time(0, 0))
    day_end   = datetime.combine(target_date, time(23, 59, 59))

    occupied = db.query(Appointment.scheduled_date).filter(
        Appointment.tenant_id == tenant_id,
        Appointment.scheduled_date >= day_start,
        Appointment.scheduled_date <= day_end,
        Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
    ).all()

    occupied_times = {row[0].strftime("%H:%M") for row in occupied}
    return {
        "date": target_date.isoformat(),
        "day_name": DAY_NAMES.get(day_of_week, ""),
        "slots": [s for s in all_slots if s not in occupied_times],
    }


# ── CRUD ──────────────────────────────────────────────────────────────────────

def create_appointment(db: Session, tenant_id: str, data: AppointmentCreate) -> Appointment:
    patient_id = data.patient_id
    if not patient_id and data.patient_phone:
        patient_id = _get_or_create_patient(db, tenant_id, data.patient_phone, data.patient_name)

    appt = Appointment(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        patient_id=patient_id,
        dentist_name=data.dentist_name,
        procedure=data.procedure,
        value=data.value or 0.0,
        scheduled_date=data.scheduled_date,
        status=AppointmentStatus.PENDING,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    logger.info(f"[tenant={tenant_id}] Agendamento criado id={appt.id}")
    return appt


def confirm_appointment(db: Session, appointment_id: str, tenant_id: str) -> Optional[Appointment]:
    appt = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.tenant_id == tenant_id,
    ).first()
    if not appt:
        return None
    appt.status = AppointmentStatus.CONFIRMED
    appt.confirmed_at = datetime.now(TZ)
    db.commit()
    db.refresh(appt)
    return appt


def cancel_appointment(db: Session, appointment_id: str, tenant_id: str) -> Optional[Appointment]:
    appt = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.tenant_id == tenant_id,
    ).first()
    if not appt:
        return None
    appt.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appt)
    return appt


def get_appointment_by_id(db: Session, appointment_id: str, tenant_id: str) -> Optional[Appointment]:
    return db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.tenant_id == tenant_id,
    ).first()


def list_appointments(
    db: Session,
    tenant_id: str,
    filter: str = "todos",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    now      = datetime.now(TZ)
    today    = now.date()
    tomorrow = today + timedelta(days=1)

    query = db.query(Appointment).filter(Appointment.tenant_id == tenant_id)

    if filter == "hoje":
        query = query.filter(
            Appointment.scheduled_date >= datetime.combine(today,    time(0, 0)),
            Appointment.scheduled_date <= datetime.combine(today,    time(23, 59, 59)),
        )
    elif filter == "amanha":
        query = query.filter(
            Appointment.scheduled_date >= datetime.combine(tomorrow, time(0, 0)),
            Appointment.scheduled_date <= datetime.combine(tomorrow, time(23, 59, 59)),
        )
    elif filter == "pendentes":
        query = query.filter(Appointment.status == AppointmentStatus.PENDING)

    total = query.count()
    items = (
        query.order_by(Appointment.scheduled_date.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_create_patient(db: Session, tenant_id: str, phone: str, name: Optional[str]) -> str:
    patient = db.query(Patient).filter(
        Patient.tenant_id == tenant_id,
        Patient.phone == phone,
    ).first()
    if patient:
        return patient.id

    patient = Patient(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        phone=phone,
        name=name or "Paciente via WhatsApp",
    )
    db.add(patient)
    db.flush()
    return patient.id