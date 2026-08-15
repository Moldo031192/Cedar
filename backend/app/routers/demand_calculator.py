from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.demand_task import DemandTask
from app.schemas.demand_calculator import (
    DemandCalculateRequest,
    DemandCalculateResponse,
)
from app.services.demand_calculator import calculate_demand_intervals


router = APIRouter(
    prefix="/demand",
    tags=["Demand Calculator"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/calculate",
    response_model=DemandCalculateResponse,
)
def calculate_demand(
    payload: DemandCalculateRequest,
    db: Session = Depends(get_db),
):
    # We intentionally query by start_time here because
    # DemandTask.end_time is a hybrid Python property,
    # not a physical database column.
    tasks = (
        db.query(DemandTask)
        .filter(
            DemandTask.organization_id == payload.organization_id,
            DemandTask.start_time < payload.end_time,
        )
        .order_by(DemandTask.start_time.asc())
        .all()
    )

    intervals = calculate_demand_intervals(
        tasks=tasks,
        window_start=payload.start_time,
        window_end=payload.end_time,
        core_capacity=payload.core_capacity,
        support_capacity=payload.support_capacity,
    )

    total_capacity = (
        payload.core_capacity
        + payload.support_capacity
    )

    return DemandCalculateResponse(
        organization_id=payload.organization_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        core_capacity=payload.core_capacity,
        support_capacity=payload.support_capacity,
        total_capacity=total_capacity,
        intervals=intervals,
    )