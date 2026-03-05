from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum


class AppointmentStatus(str, Enum):
    PENDENTE = "pendente"
    CONFIRMADO = "confirmado"
    CANCELADO = "cancelado"
    CONCLUIDO = "concluido"


# ── Request ────────────────────────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    patient_id: Optional[int] = None
    patient_phone: str                    # fallback se patient_id não existir
    patient_name: Optional[str] = None   # criado automaticamente pelo bot
    dentist_name: Optional[str] = None
    procedure: Optional[str] = None
    value: Optional[float] = None
    scheduled_date: datetime
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    dentist_name: Optional[str] = None
    procedure: Optional[str] = None
    value: Optional[float] = None
    scheduled_date: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None


# ── Response ───────────────────────────────────────────────────────────────────

class AppointmentOut(BaseModel):
    id: int
    tenant_id: int
    patient_id: Optional[int]
    patient_name: Optional[str]
    patient_phone: str
    dentist_name: Optional[str]
    procedure: Optional[str]
    value: Optional[float]
    scheduled_date: datetime
    status: AppointmentStatus
    notes: Optional[str]
    created_at: datetime
    confirmed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AvailableSlotsResponse(BaseModel):
    date: str
    slots: list[str]   # lista de horários no formato "HH:MM"
    day_name: str