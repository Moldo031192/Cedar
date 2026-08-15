import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.db.session import SessionLocal
from app.models.demand_task import DemandTask
from app.models.employee import Employee
from app.schemas.workforce_coverage import (
    WorkforceCoverageRequest,
    WorkforceCoverageResponse,
)
from app.services.workforce_coverage import (
    calculate_workforce_coverage,
)


router = APIRouter(
    prefix="/workforce",
    tags=["Workforce Coverage"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/coverage",
    response_model=WorkforceCoverageResponse,
)
def workforce_coverage(
    payload: WorkforceCoverageRequest,
    db: Session = Depends(get_db),
):
    tasks = (
        db.query(DemandTask)
        .options(
            selectinload(DemandTask.required_qualifications)
        )
        .filter(
            DemandTask.organization_id == payload.organization_id,
            DemandTask.start_time < payload.end_time,
        )
        .order_by(DemandTask.start_time.asc())
        .all()
    )

    employees = (
        db.query(Employee)
        .options(
            selectinload(Employee.employee_qualifications)
        )
        .filter(
            Employee.organization_id == payload.organization_id,
            Employee.is_active.is_(True),
        )
        .order_by(Employee.employee_number.asc())
        .all()
    )

    intervals, eligible_employees = calculate_workforce_coverage(
        tasks=tasks,
        employees=employees,
        window_start=payload.start_time,
        window_end=payload.end_time,
        available_headcount=payload.available_headcount,
    )

    return WorkforceCoverageResponse(
        organization_id=payload.organization_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        available_headcount=payload.available_headcount,
        intervals=intervals,
        eligible_employees=eligible_employees,
    )