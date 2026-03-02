from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Float, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.core.database import Base

class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"          # novo: faltou

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    patient = relationship("Patient", back_populates="appointments")
    dentist_name = Column(String, nullable=True)
    procedure = Column(String, nullable=True)
    value = Column(Float, default=0.0)                    # ← novo: valor da consulta
    
    scheduled_date = Column(DateTime, nullable=False)
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.PENDING)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="appointments")

    # Índices para performance em produção
    __table_args__ = (
        Index("ix_appointment_tenant_date", "tenant_id", "scheduled_date"),
        Index("ix_appointment_status", "status"),
    )