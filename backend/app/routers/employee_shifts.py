import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.employee_shift import EmployeeShift
from app.models.employee import Employee
from app.models.shift import Shift
from app.schemas.employee_shift import (
    EmployeeShiftCreate,
    EmployeeShiftUpdate,
    EmployeeShiftResponse,
)

router = APIRouter(prefix="/employee-shifts", tags=["Employee Shifts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[EmployeeShiftResponse])
def list_employee_shifts(
    employee_id: uuid.UUID | None = None,
    shift_id: uuid.UUID | None = None,
    work_date: date | None = None,
    work_date_from: date | None = None,
    work_date_to: date | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(EmployeeShift)

    if employee_id is not None:
        query = query.filter(EmployeeShift.employee_id == employee_id)
    if shift_id is not None:
        query = query.filter(EmployeeShift.shift_id == shift_id)
    if work_date is not None:
        query = query.filter(EmployeeShift.work_date == work_date)
    if work_date_from is not None:
        query = query.filter(EmployeeShift.work_date >= work_date_from)
    if work_date_to is not None:
        query = query.filter(EmployeeShift.work_date <= work_date_to)

    return query.order_by(EmployeeShift.created_at.desc()).all()


@router.get("/{employee_shift_id}", response_model=EmployeeShiftResponse)
def get_employee_shift(employee_shift_id: uuid.UUID, db: Session = Depends(get_db)):
    employee_shift = db.query(EmployeeShift).filter(EmployeeShift.id == employee_shift_id).first()
    if not employee_shift:
        raise HTTPException(status_code=404, detail="Employee shift not found")
    return employee_shift


@router.post("", response_model=EmployeeShiftResponse, status_code=status.HTTP_201_CREATED)
def create_employee_shift(payload: EmployeeShiftCreate, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if not employee:
        raise HTTPException(status_code=400, detail="Employee not found")

    shift = db.query(Shift).filter(Shift.id == payload.shift_id).first()
    if not shift:
        raise HTTPException(status_code=400, detail="Shift not found")

    if employee.organization_id != shift.organization_id:
        raise HTTPException(status_code=400, detail="Employee and shift must belong to the same organization")

    existing = (
        db.query(EmployeeShift)
        .filter(
            EmployeeShift.employee_id == payload.employee_id,
            EmployeeShift.work_date == payload.work_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Employee already has a shift assigned for this work_date")

    employee_shift = EmployeeShift(
        employee_id=payload.employee_id,
        shift_id=payload.shift_id,
        work_date=payload.work_date,
        is_support=payload.is_support,
        is_present=payload.is_present,
        notes=payload.notes,
    )

    db.add(employee_shift)
    db.commit()
    db.refresh(employee_shift)
    return employee_shift


@router.put("/{employee_shift_id}", response_model=EmployeeShiftResponse)
def update_employee_shift(
    employee_shift_id: uuid.UUID,
    payload: EmployeeShiftUpdate,
    db: Session = Depends(get_db),
):
    employee_shift = db.query(EmployeeShift).filter(EmployeeShift.id == employee_shift_id).first()
    if not employee_shift:
        raise HTTPException(status_code=404, detail="Employee shift not found")

    new_employee_id = payload.employee_id if payload.employee_id is not None else employee_shift.employee_id
    new_shift_id = payload.shift_id if payload.shift_id is not None else employee_shift.shift_id

    employee = None
    if payload.employee_id is not None:
        employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
        if not employee:
            raise HTTPException(status_code=400, detail="Employee not found")

    shift = None
    if payload.shift_id is not None:
        shift = db.query(Shift).filter(Shift.id == payload.shift_id).first()
        if not shift:
            raise HTTPException(status_code=400, detail="Shift not found")

    if payload.employee_id is not None or payload.shift_id is not None:
        if employee is None:
            employee = db.query(Employee).filter(Employee.id == new_employee_id).first()
        if shift is None:
            shift = db.query(Shift).filter(Shift.id == new_shift_id).first()
        if employee.organization_id != shift.organization_id:
            raise HTTPException(status_code=400, detail="Employee and shift must belong to the same organization")

    new_work_date = payload.work_date if payload.work_date is not None else employee_shift.work_date

    if new_employee_id != employee_shift.employee_id or new_work_date != employee_shift.work_date:
        existing = (
            db.query(EmployeeShift)
            .filter(
                EmployeeShift.employee_id == new_employee_id,
                EmployeeShift.work_date == new_work_date,
                EmployeeShift.id != employee_shift.id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Employee already has a shift assigned for this work_date")

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(employee_shift, field, value)

    db.commit()
    db.refresh(employee_shift)
    return employee_shift


@router.delete("/{employee_shift_id}")
def delete_employee_shift(employee_shift_id: uuid.UUID, db: Session = Depends(get_db)):
    employee_shift = db.query(EmployeeShift).filter(EmployeeShift.id == employee_shift_id).first()
    if not employee_shift:
        raise HTTPException(status_code=404, detail="Employee shift not found")

    db.delete(employee_shift)
    db.commit()
    return {"message": "Employee shift deleted successfully"}