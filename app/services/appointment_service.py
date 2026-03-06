"""
Serviço de agendamentos da OdontoIA.

Responsabilidades:
- Calcular slots disponíveis para uma data (com base em clinic_hours)
- Criar agendamento (status=pendente)
- Confirmar / cancelar agendamento
- Listar agendamentos com filtros
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
from app.core.auth import get_current_user

from app.models.clinic_hours import ClinicHours, DAY_NAMES
from app.models.appointment import Appointment          # modelo existente
from app.models.patient import Patient                  # modelo existente
from app.schemas.appointment import AppointmentCreate, AppointmentStatus

logger = logging.getLogger(__name__)

# Fuso horário padrão — ajuste conforme necessário
TZ = ZoneInfo("America/Sao_Paulo")


# ─────────────────────────────────────────────────────────────────────────────
# Disponibilidade
# ─────────────────────────────────────────────────────────────────────────────

def get_clinic_hours_for_day(db: Session, tenant_id: int, day_of_week: int) -> Optional[ClinicHours]:
    """Retorna as configurações de horário para um dia da semana."""
    result = db.execute(
        select(ClinicHours).where(
            and_(
                ClinicHours.tenant_id == tenant_id,
                ClinicHours.day_of_week == day_of_week,
                ClinicHours.is_active == True,
            )
        )
    )
    return result.scalar_one_or_none()


def _generate_slots(start: time, end: time, duration_minutes: int) -> list[str]:
    """Gera lista de horários no formato HH:MM dado início, fim e duração."""
    slots = []
    current = datetime.combine(date.today(), start)
    end_dt = datetime.combine(date.today(), end)
    delta = timedelta(minutes=duration_minutes)

    while current + delta <= end_dt:
        slots.append(current.strftime("%H:%M"))
        current += delta
    return slots


def get_available_slots(
    db: Session,
    tenant_id: int,
    target_date: date,
) -> dict:
    """
    Retorna slots disponíveis para uma data específica.
    Desconta horários já ocupados por agendamentos confirmados/pendentes.
    """
    day_of_week = target_date.weekday()  # 0=Segunda … 6=Domingo
    hours = get_clinic_hours_for_day(db, tenant_id, day_of_week)

    if not hours:
        return {
            "date": target_date.isoformat(),
            "day_name": DAY_NAMES.get(day_of_week, ""),
            "slots": [],
            "message": "Clínica não atende neste dia.",
        }

    all_slots = _generate_slots(hours.start_time, hours.end_time, hours.slot_duration_minutes)

    # Busca agendamentos já existentes neste dia
    day_start = datetime.combine(target_date, time(0, 0))
    day_end = datetime.combine(target_date, time(23, 59, 59))

    result = db.execute(
        select(Appointment.scheduled_date).where(
            and_(
                Appointment.tenant_id == tenant_id,
                Appointment.scheduled_date >= day_start,
                Appointment.scheduled_date <= day_end,
                Appointment.status.in_(
                    [AppointmentStatus.PENDENTE, AppointmentStatus.CONFIRMADO]
                ),
            )
        )
    )
    occupied_times = {row[0].strftime("%H:%M") for row in result.fetchall()}

    available = [s for s in all_slots if s not in occupied_times]

    return {
        "date": target_date.isoformat(),
        "day_name": DAY_NAMES.get(day_of_week, ""),
        "slots": available,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CRUD de agendamentos
# ─────────────────────────────────────────────────────────────────────────────

def create_appointment(
    db: Session,
    tenant_id: int,
    data: AppointmentCreate,
) -> Appointment:
    """
    Cria um agendamento com status PENDENTE.
    Se patient_id não fornecido, cria ou busca paciente pelo telefone.
    """
    patient_id = data.patient_id

    if not patient_id and data.patient_phone:
        patient_id = _get_or_create_patient(
            db, tenant_id, data.patient_phone, data.patient_name
        )

    appt = Appointment(
        tenant_id=tenant_id,
        patient_id=patient_id,
        patient_phone=data.patient_phone,
        dentist_name=data.dentist_name,
        procedure=data.procedure,
        value=data.value,
        scheduled_date=data.scheduled_date,
        status=AppointmentStatus.PENDENTE,
        notes=data.notes,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    logger.info(f"[tenant={tenant_id}] Agendamento criado id={appt.id} para {data.patient_phone}")
    return appt


def confirm_appointment(db:Session, appointment_id: int, tenant_id: int) -> Optional[Appointment]:
    """Confirma um agendamento pendente."""
    result = db.execute(
        select(Appointment).where(
            and_(Appointment.id == appointment_id, Appointment.tenant_id == tenant_id)
        )
    )
    appt = result.scalar_one_or_none()
    if not appt:
        return None

    appt.status = AppointmentStatus.CONFIRMADO
    appt.confirmed_at = datetime.now(TZ)
    db.commit()
    db.refresh(appt)
    return appt


def cancel_appointment(db: Session, appointment_id: int, tenant_id: int) -> Optional[Appointment]:
    """Cancela um agendamento."""
    result = db.execute(
        select(Appointment).where(
            and_(Appointment.id == appointment_id, Appointment.tenant_id == tenant_id)
        )
    )
    appt = result.scalar_one_or_none()
    if not appt:
        return None

    appt.status = AppointmentStatus.CANCELADO
    db.commit()
    db.refresh(appt)
    return appt


def list_appointments(
    db: Session,
    tenant_id: int,
    filter: str = "todos",     # "hoje" | "amanha" | "pendentes" | "todos"
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Lista agendamentos com filtros e paginação."""
    now = datetime.now(TZ)
    today = now.date()
    tomorrow = today + timedelta(days=1)

    query = select(Appointment).where(Appointment.tenant_id == tenant_id)

    if filter == "hoje":
        query = query.where(
            and_(
                Appointment.scheduled_date >= datetime.combine(today, time(0, 0)),
                Appointment.scheduled_date <= datetime.combine(today, time(23, 59, 59)),
            )
        )
    elif filter == "amanha":
        query = query.where(
            and_(
                Appointment.scheduled_date >= datetime.combine(tomorrow, time(0, 0)),
                Appointment.scheduled_date <= datetime.combine(tomorrow, time(23, 59, 59)),
            )
        )
    elif filter == "pendentes":
        query = query.where(Appointment.status == AppointmentStatus.PENDENTE)

    count_query = select(func.count()).select_from(query.subquery())
    total = (db.execute(count_query)).scalar_one()

    query = (
        query
        .order_by(Appointment.scheduled_date.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = db.execute(query)
    items = result.scalars().all()

    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _get_or_create_patient(
    db: Session, tenant_id: int, phone: str, name: Optional[str]
) -> int:
    """Busca paciente pelo telefone ou cria um novo registro."""
    result = db.execute(
        select(Patient).where(
            and_(Patient.tenant_id == tenant_id, Patient.phone == phone)
        )
    )
    patient = result.scalar_one_or_none()
    if patient:
        return patient.id

    patient = Patient(
        tenant_id=tenant_id,
        phone=phone,
        name=name or "Paciente via WhatsApp",
    )
    db.add(patient)
    db.flush()
    return patient.id


def get_appointment_by_id(db: Session, appointment_id: int, tenant_id: int) -> Optional[Appointment]:
    result = db.execute(
        select(Appointment).where(
            and_(Appointment.id == appointment_id, Appointment.tenant_id == tenant_id)
        )
    )
    return result.scalar_one_or_none()