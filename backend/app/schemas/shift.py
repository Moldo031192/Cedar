import uuid
from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, model_validator


class ShiftCreate(BaseModel):
    organization_id: uuid.UUID
    name: str
    code: str
    start_time: time
    end_time: time
    crosses_midnight: bool = False
    target_headcount: int = 14
    support_headcount: int = 0
    is_active: bool = True

    @model_validator(mode="after")
    def validate_time_semantics(self):
        if self.start_time == self.end_time:
            raise ValueError("start_time and end_time cannot be equal")
        if self.crosses_midnight:
            if self.start_time <= self.end_time:
                raise ValueError(
                    "when crosses_midnight is true, start_time must be greater than end_time"
                )
        else:
            if self.start_time >= self.end_time:
                raise ValueError(
                    "when crosses_midnight is false, start_time must be less than end_time"
                )
        return self


class ShiftUpdate(BaseModel):
    organization_id: uuid.UUID | None = None
    name: str | None = None
    code: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    crosses_midnight: bool | None = None
    target_headcount: int | None = None
    support_headcount: int | None = None
    is_active: bool | None = None


class ShiftResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    code: str
    start_time: time
    end_time: time
    crosses_midnight: bool
    target_headcount: int
    support_headcount: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)