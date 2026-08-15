import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, model_validator


class DemandTaskType(str, Enum):
    DEBOARDING = "DEBOARDING"
    BOARDING = "BOARDING"
    TURNAROUND = "TURNAROUND"


class DemandTaskStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class DemandTaskCreate(BaseModel):
    organization_id: uuid.UUID
    flight_reference: str
    task_type: DemandTaskType
    start_time: datetime
    duration_minutes: int
    target_headcount: int
    minimum_headcount: int
    airline_contract_reference: str | None = None
    status: DemandTaskStatus = DemandTaskStatus.PLANNED
    required_qualification_ids: list[uuid.UUID] = []

    @model_validator(mode="after")
    def validate_business_rules(self):
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be greater than zero")
        if self.minimum_headcount < 0 or self.target_headcount < 0:
            raise ValueError("headcount values cannot be negative")
        if self.minimum_headcount > self.target_headcount:
            raise ValueError("minimum_headcount cannot be greater than target_headcount")
        return self


class DemandTaskUpdate(BaseModel):
    organization_id: uuid.UUID | None = None
    flight_reference: str | None = None
    task_type: DemandTaskType | None = None
    start_time: datetime | None = None
    duration_minutes: int | None = None
    target_headcount: int | None = None
    minimum_headcount: int | None = None
    airline_contract_reference: str | None = None
    status: DemandTaskStatus | None = None
    required_qualification_ids: list[uuid.UUID] | None = None


class DemandTaskResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    flight_reference: str
    task_type: DemandTaskType
    start_time: datetime
    duration_minutes: int
    end_time: datetime
    target_headcount: int
    minimum_headcount: int
    airline_contract_reference: str | None = None
    status: DemandTaskStatus
    required_qualification_ids: list[uuid.UUID] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
