import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class EmployeeQualificationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"


class EmployeeQualificationCreate(BaseModel):
    employee_id: uuid.UUID
    qualification_id: uuid.UUID
    obtained_at: date
    expires_at: date | None = None
    status: EmployeeQualificationStatus
    notes: str | None = None


class EmployeeQualificationUpdate(BaseModel):
    employee_id: uuid.UUID | None = None
    qualification_id: uuid.UUID | None = None
    obtained_at: date | None = None
    expires_at: date | None = None
    status: EmployeeQualificationStatus | None = None
    notes: str | None = None


class EmployeeQualificationResponse(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    qualification_id: uuid.UUID
    obtained_at: date
    expires_at: date | None = None
    status: EmployeeQualificationStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
