import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class EmployeeShiftCreate(BaseModel):
    employee_id: uuid.UUID
    shift_id: uuid.UUID
    work_date: date
    is_support: bool = False
    is_present: bool = True
    notes: str | None = None


class EmployeeShiftUpdate(BaseModel):
    employee_id: uuid.UUID | None = None
    shift_id: uuid.UUID | None = None
    work_date: date | None = None
    is_support: bool | None = None
    is_present: bool | None = None
    notes: str | None = None


class EmployeeShiftResponse(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    shift_id: uuid.UUID
    work_date: date
    is_support: bool
    is_present: bool
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)