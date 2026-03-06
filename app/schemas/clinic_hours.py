from datetime import time
from typing import Optional
from pydantic import BaseModel, validator


class ClinicHoursBase(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration_minutes: int = 30
    is_active: bool = True

    @validator("day_of_week")
    def validate_day(cls, v):
        if v not in range(7):
            raise ValueError("day_of_week deve estar entre 0 e 6")
        return v

    @validator("end_time")
    def validate_end_after_start(cls, v, values):
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("end_time deve ser maior que start_time")
        return v


class ClinicHoursCreate(ClinicHoursBase):
    pass


class ClinicHoursUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    slot_duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class ClinicHoursOut(ClinicHoursBase):
    id: str
    tenant_id: str
    day_name: str = ""

    class Config:
        from_attributes = True