from sqlalchemy import Column, String, Boolean, DateTime, func
from app.models.appointment import relationship
from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    human_mode_active = Column(Boolean, default=False)
    human_mode_until = Column(DateTime, nullable=True)
    dentist_name = Column(String, nullable=False)
    whatsapp_number = Column(String, unique=True, nullable=False)
    twilio_sid = Column(String, nullable=True)
    plan = Column(String, default="basic")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    attendant_phone = Column(String, nullable=True)

    # ── nova coluna ──────────────────────────────────────────
    api_key = Column(String, unique=True, nullable=True, index=True)
    # nullable=True para não quebrar tenants existentes antes da migração

    appointments = relationship("Appointment", back_populates="tenant", cascade="all, delete-orphan")
    patients = relationship("Patient", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant {self.name}>"