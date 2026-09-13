from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.db.session import SessionLocal
from app.models.demand_task import DemandTask
from app.models.employee import Employee
from app.models.employee_shift import EmployeeShift
from app.models.shift import Shift
from app.schemas.workforce_coverage import (
    WorkforceCoverageRequest,
    WorkforceCoverageResponse,
)
from app.services.workforce_coverage import calculate_workforce_coverage


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
        .options(selectinload(DemandTask.required_qualifications))
        .filter(
            DemandTask.organization_id == payload.organization_id,
            DemandTask.start_time < payload.end_time,
        )
        .order_by(DemandTask.start_time.asc())
        .all()
    )

    window_start_date = payload.start_time.date()
    window_end_date = payload.end_time.date()

    employee_shifts = (
        db.query(EmployeeShift)
        .join(Employee, EmployeeShift.employee_id == Employee.id)
        .join(Shift, EmployeeShift.shift_id == Shift.id)
        .options(
            selectinload(EmployeeShift.employee).selectinload(
                Employee.employee_qualifications
            ),
            selectinload(EmployeeShift.shift),
        )
        .filter(
            Employee.organization_id == payload.organization_id,
            Shift.organization_id == payload.organization_id,
            EmployeeShift.work_date >= window_start_date - timedelta(days=1),
            EmployeeShift.work_date <= window_end_date,
        )
        .order_by(EmployeeShift.work_date.asc())
        .all()
    )

    intervals, task_eligibility = calculate_workforce_coverage(
        tasks=tasks,
        employee_shifts=employee_shifts,
        window_start=payload.start_time,
        window_end=payload.end_time,
    )

    return WorkforceCoverageResponse(
        organization_id=payload.organization_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        intervals=intervals,
        task_eligibility=task_eligibility,
    )