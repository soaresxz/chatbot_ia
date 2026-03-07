from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default="clinic_user")  # "super_admin" | "clinic_user"
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True)  # null para super_admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    tenant = relationship("Tenant", back_populates="users")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"