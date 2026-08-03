import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class QualificationCreate(BaseModel):
    organization_id: uuid.UUID
    name: str
    code: str
    description: str | None = None
    requires_expiration: bool = False
    default_validity_months: int | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_expiration_rules(self):
        if self.requires_expiration and self.default_validity_months is None:
            raise ValueError("default_validity_months is required when requires_expiration is true")
        if not self.requires_expiration and self.default_validity_months is not None:
            raise ValueError("default_validity_months must be null when requires_expiration is false")
        return self


class QualificationUpdate(BaseModel):
    organization_id: uuid.UUID | None = None
    name: str | None = None
    code: str | None = None
    description: str | None = None
    requires_expiration: bool | None = None
    default_validity_months: int | None = None
    is_active: bool | None = None


class QualificationResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    code: str
    description: str | None = None
    requires_expiration: bool
    default_validity_months: int | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
