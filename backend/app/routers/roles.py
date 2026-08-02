import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse

router = APIRouter(prefix="/roles", tags=["Roles"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[RoleResponse])
def list_roles(db: Session = Depends(get_db)):
    return db.query(Role).order_by(Role.created_at.desc()).all()


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(role_id: uuid.UUID, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreate, db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == payload.organization_id).first()
    if not organization:
        raise HTTPException(status_code=400, detail="Organization not found")

    existing = db.query(Role).filter(Role.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role code already exists")

    role = Role(
        organization_id=payload.organization_id,
        name=payload.name,
        code=payload.code,
        description=payload.description,
        is_active=payload.is_active,
    )

    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(role_id: uuid.UUID, payload: RoleUpdate, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if payload.organization_id:
        organization = db.query(Organization).filter(Organization.id == payload.organization_id).first()
        if not organization:
            raise HTTPException(status_code=400, detail="Organization not found")

    if payload.code and payload.code != role.code:
        existing = db.query(Role).filter(Role.code == payload.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Role code already exists")

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(role, field, value)

    db.commit()
    db.refresh(role)
    return role


@router.delete("/{role_id}")
def delete_role(role_id: uuid.UUID, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    db.delete(role)
    db.commit()
    return {"message": "Role deleted successfully"}
