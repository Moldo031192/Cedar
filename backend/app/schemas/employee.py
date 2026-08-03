import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr


class EmploymentType(str, Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"


class EmployeeCreate(BaseModel):
    organization_id: uuid.UUID
    department_id: uuid.UUID
    role_id: uuid.UUID
    employee_number: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    employment_type: EmploymentType
    hire_date: date
    is_active: bool = True


class EmployeeUpdate(BaseModel):
    organization_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
    employee_number: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    employment_type: EmploymentType | None = None
    hire_date: date | None = None
    is_active: bool | None = None


class EmployeeResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    department_id: uuid.UUID
    role_id: uuid.UUID
    employee_number: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    employment_type: EmploymentType
    hire_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
