import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[OrganizationResponse])
def list_organizations(db: Session = Depends(get_db)):
    return db.query(Organization).order_by(Organization.created_at.desc()).all()


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(organization_id: uuid.UUID, db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)):
    existing = db.query(Organization).filter(Organization.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Organization code already exists")

    organization = Organization(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        is_active=payload.is_active,
    )

    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


@router.put("/{organization_id}", response_model=OrganizationResponse)
def update_organization(
    organization_id: uuid.UUID,
    payload: OrganizationUpdate,
    db: Session = Depends(get_db),
):
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    if payload.code and payload.code != organization.code:
        existing = db.query(Organization).filter(Organization.code == payload.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Organization code already exists")

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(organization, field, value)

    db.commit()
    db.refresh(organization)
    return organization


@router.delete("/{organization_id}")
def delete_organization(organization_id: uuid.UUID, db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    db.delete(organization)
    db.commit()
    return {"message": "Organization deleted successfully"}
