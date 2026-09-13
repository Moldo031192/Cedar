import uuid
from datetime import datetime

from pydantic import BaseModel, model_validator


class WorkforceCoverageRequest(BaseModel):
    organization_id: uuid.UUID
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class CoverageInterval(BaseModel):
    start_time: datetime
    end_time: datetime

    target_demand: int
    minimum_demand: int

    scheduled_workforce: int

    target_gap: int
    minimum_gap: int

    status: str


class TaskEmployeeEligibility(BaseModel):
    employee_id: uuid.UUID
    employee_number: str
    employee_name: str

    eligible: bool
    missing_qualification_ids: list[uuid.UUID] = []


class TaskEligibility(BaseModel):
    task_id: uuid.UUID
    flight_reference: str
    start_time: datetime
    end_time: datetime

    employees: list[TaskEmployeeEligibility] = []


class WorkforceCoverageResponse(BaseModel):
    organization_id: uuid.UUID

    start_time: datetime
    end_time: datetime

    intervals: list[CoverageInterval]
    task_eligibility: list[TaskEligibility]