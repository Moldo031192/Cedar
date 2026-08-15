import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class DemandCalculateRequest(BaseModel):
    organization_id: uuid.UUID

    start_time: datetime
    end_time: datetime

    core_capacity: int = Field(default=14, ge=0)
    support_capacity: int = Field(default=5, ge=0)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")

        return self


class DemandInterval(BaseModel):
    start_time: datetime
    end_time: datetime

    target_demand: int
    minimum_demand: int

    core_capacity: int
    support_capacity: int
    total_capacity: int

    target_gap: int
    minimum_gap: int

    target_status: str
    minimum_status: str


class DemandCalculateResponse(BaseModel):
    organization_id: uuid.UUID

    start_time: datetime
    end_time: datetime

    core_capacity: int
    support_capacity: int
    total_capacity: int

    intervals: list[DemandInterval]