   
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import uuid

class ConversationStatus(Base):
    __tablename__ = "conversation_status"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    patient_phone = Column(String, nullable=False, index=True)

    human_mode_active = Column(Boolean, default=False)
    human_mode_until = Column(DateTime, nullable=True)

    pending_confirmation = Column(JSONB, nullable=True)
    message_log = Column(JSONB, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant")