import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.department import Department
from app.models.employee import Employee
from app.models.organization import Organization
from app.models.role import Role
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse

router = APIRouter(prefix="/employees", tags=["Employees"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[EmployeeResponse])
def list_employees(db: Session = Depends(get_db)):
    return db.query(Employee).order_by(Employee.created_at.desc()).all()


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == payload.organization_id).first()
    if not organization:
        raise HTTPException(status_code=400, detail="Organization not found")

    department = db.query(Department).filter(Department.id == payload.department_id).first()
    if not department:
        raise HTTPException(status_code=400, detail="Department not found")

    role = db.query(Role).filter(Role.id == payload.role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail="Role not found")

    existing_number = db.query(Employee).filter(Employee.employee_number == payload.employee_number).first()
    if existing_number:
        raise HTTPException(status_code=400, detail="Employee number already exists")

    existing_email = db.query(Employee).filter(Employee.email == payload.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Employee email already exists")

    employee = Employee(
        organization_id=payload.organization_id,
        department_id=payload.department_id,
        role_id=payload.role_id,
        employee_number=payload.employee_number,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
        employment_type=payload.employment_type,
        hire_date=payload.hire_date,
        is_active=payload.is_active,
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: uuid.UUID, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if payload.organization_id:
        organization = db.query(Organization).filter(Organization.id == payload.organization_id).first()
        if not organization:
            raise HTTPException(status_code=400, detail="Organization not found")

    if payload.department_id:
        department = db.query(Department).filter(Department.id == payload.department_id).first()
        if not department:
            raise HTTPException(status_code=400, detail="Department not found")

    if payload.role_id:
        role = db.query(Role).filter(Role.id == payload.role_id).first()
        if not role:
            raise HTTPException(status_code=400, detail="Role not found")

    if payload.employee_number and payload.employee_number != employee.employee_number:
        existing_number = db.query(Employee).filter(Employee.employee_number == payload.employee_number).first()
        if existing_number:
            raise HTTPException(status_code=400, detail="Employee number already exists")

    if payload.email and payload.email != employee.email:
        existing_email = db.query(Employee).filter(Employee.email == payload.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Employee email already exists")

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)
    return employee


@router.delete("/{employee_id}")
def delete_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.delete(employee)
    db.commit()
    return {"message": "Employee deleted successfully"}
