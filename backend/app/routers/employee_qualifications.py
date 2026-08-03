import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.employee import Employee
from app.models.employee_qualification import EmployeeQualification
from app.models.qualification import Qualification
from app.schemas.employee_qualification import (
    EmployeeQualificationCreate,
    EmployeeQualificationUpdate,
    EmployeeQualificationResponse,
)

router = APIRouter(prefix="/employee-qualifications", tags=["EmployeeQualifications"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[EmployeeQualificationResponse])
def list_employee_qualifications(db: Session = Depends(get_db)):
    return db.query(EmployeeQualification).order_by(EmployeeQualification.created_at.desc()).all()


@router.get("/{employee_qualification_id}", response_model=EmployeeQualificationResponse)
def get_employee_qualification(employee_qualification_id: uuid.UUID, db: Session = Depends(get_db)):
    item = db.query(EmployeeQualification).filter(EmployeeQualification.id == employee_qualification_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Employee qualification not found")
    return item


@router.post("", response_model=EmployeeQualificationResponse, status_code=status.HTTP_201_CREATED)
def create_employee_qualification(payload: EmployeeQualificationCreate, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if not employee:
        raise HTTPException(status_code=400, detail="Employee not found")

    qualification = db.query(Qualification).filter(Qualification.id == payload.qualification_id).first()
    if not qualification:
        raise HTTPException(status_code=400, detail="Qualification not found")

    item = EmployeeQualification(
        employee_id=payload.employee_id,
        qualification_id=payload.qualification_id,
        obtained_at=payload.obtained_at,
        expires_at=payload.expires_at,
        status=payload.status,
        notes=payload.notes,
    )

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{employee_qualification_id}", response_model=EmployeeQualificationResponse)
def update_employee_qualification(
    employee_qualification_id: uuid.UUID,
    payload: EmployeeQualificationUpdate,
    db: Session = Depends(get_db),
):
    item = db.query(EmployeeQualification).filter(EmployeeQualification.id == employee_qualification_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Employee qualification not found")

    if payload.employee_id:
        employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
        if not employee:
            raise HTTPException(status_code=400, detail="Employee not found")

    if payload.qualification_id:
        qualification = db.query(Qualification).filter(Qualification.id == payload.qualification_id).first()
        if not qualification:
            raise HTTPException(status_code=400, detail="Qualification not found")

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{employee_qualification_id}")
def delete_employee_qualification(employee_qualification_id: uuid.UUID, db: Session = Depends(get_db)):
    item = db.query(EmployeeQualification).filter(EmployeeQualification.id == employee_qualification_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Employee qualification not found")

    db.delete(item)
    db.commit()
    return {"message": "Employee qualification deleted successfully"}
