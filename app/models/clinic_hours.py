import uuid

from sqlalchemy import Column, Integer, String, Time, Boolean, ForeignKey, UniqueConstraint
from app.core.database import Base

DAY_NAMES = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}


class ClinicHours(Base):
    """
    Define os horários de funcionamento da clínica por dia da semana.
    Cada registro representa um dia com início, fim e duração do slot.
    Ex: Segunda, 08:00–18:00, 30 min → 20 slots disponíveis.
    """
    __tablename__ = "clinic_hours"
    __table_args__ = (
        UniqueConstraint("tenant_id", "day_of_week", name="uq_tenant_day"),
    )

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)          # 0=Segunda … 6=Domingo
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration_minutes = Column(Integer, default=30, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)