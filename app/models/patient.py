from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    tenant = relationship("Tenant", back_populates="patients")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")