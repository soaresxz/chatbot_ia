from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum


# Espelha exatamente o enum do models/appointment.py
class AppointmentStatus(str, Enum):
    PENDING   = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW   = "no_show"


# ── Request ───────────────────────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    patient_id: Optional[str] = None    # UUID — se None, cria pelo phone
    patient_phone: Optional[str] = None # usado pelo bot para achar/criar paciente
    patient_name: Optional[str] = None  # usado pelo bot ao criar paciente novo
    dentist_name: Optional[str] = None
    procedure: Optional[str] = None
    value: Optional[float] = None
    scheduled_date: datetime


class AppointmentUpdate(BaseModel):
    dentist_name: Optional[str] = None
    procedure: Optional[str] = None
    value: Optional[float] = None
    scheduled_date: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None


# ── Response ──────────────────────────────────────────────────────────────────

class AppointmentOut(BaseModel):
    id: str
    tenant_id: str
    patient_id: str
    dentist_name: Optional[str]
    procedure: Optional[str]
    value: Optional[float]
    scheduled_date: datetime
    status: AppointmentStatus
    created_at: datetime
    confirmed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AvailableSlotsResponse(BaseModel):
    date: str
    slots: list[str]
    day_name: str