import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.department import Department
from app.models.organization import Organization
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
)

router = APIRouter(prefix="/departments", tags=["Departments"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[DepartmentResponse])
def list_departments(db: Session = Depends(get_db)):
    return db.query(Department).order_by(Department.created_at.desc()).all()


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(department_id: uuid.UUID, db: Session = Depends(get_db)):
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == payload.organization_id).first()
    if not organization:
        raise HTTPException(status_code=400, detail="Organization not found")

    existing = db.query(Department).filter(Department.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department code already exists")

    department = Department(
        organization_id=payload.organization_id,
        name=payload.name,
        code=payload.code,
        description=payload.description,
        is_active=payload.is_active,
    )

    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    db: Session = Depends(get_db),
):
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    if payload.organization_id:
        organization = db.query(Organization).filter(Organization.id == payload.organization_id).first()
        if not organization:
            raise HTTPException(status_code=400, detail="Organization not found")

    if payload.code and payload.code != department.code:
        existing = db.query(Department).filter(Department.code == payload.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Department code already exists")

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(department, field, value)

    db.commit()
    db.refresh(department)
    return department


@router.delete("/{department_id}")
def delete_department(department_id: uuid.UUID, db: Session = Depends(get_db)):
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    db.delete(department)
    db.commit()
    return {"message": "Department deleted successfully"}
