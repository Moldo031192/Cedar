import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class WorkforceCoverageRequest(BaseModel):
    organization_id: uuid.UUID

    start_time: datetime
    end_time: datetime

    available_headcount: int = Field(default=14, ge=0)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")

        return self


class EmployeeCoverage(BaseModel):
    employee_id: uuid.UUID
    employee_number: str
    employee_name: str

    eligible: bool
    missing_qualification_ids: list[uuid.UUID] = []


class CoverageInterval(BaseModel):
    start_time: datetime
    end_time: datetime

    target_demand: int
    minimum_demand: int

    available_headcount: int

    target_gap: int
    minimum_gap: int

    status: str


class WorkforceCoverageResponse(BaseModel):
    organization_id: uuid.UUID

    start_time: datetime
    end_time: datetime

    available_headcount: int

    intervals: list[CoverageInterval]

    eligible_employees: list[EmployeeCoverage]