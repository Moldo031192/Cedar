import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.qualification import Qualification
from app.schemas.qualification import (
    QualificationCreate,
    QualificationUpdate,
    QualificationResponse,
)

router = APIRouter(prefix="/qualifications", tags=["Qualifications"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[QualificationResponse])
def list_qualifications(db: Session = Depends(get_db)):
    return db.query(Qualification).order_by(Qualification.created_at.desc()).all()


@router.get("/{qualification_id}", response_model=QualificationResponse)
def get_qualification(qualification_id: uuid.UUID, db: Session = Depends(get_db)):
    qualification = db.query(Qualification).filter(Qualification.id == qualification_id).first()
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")
    return qualification


@router.post("", response_model=QualificationResponse, status_code=status.HTTP_201_CREATED)
def create_qualification(payload: QualificationCreate, db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == payload.organization_id).first()
    if not organization:
        raise HTTPException(status_code=400, detail="Organization not found")

    existing = db.query(Qualification).filter(Qualification.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Qualification code already exists")

    qualification = Qualification(
        organization_id=payload.organization_id,
        name=payload.name,
        code=payload.code,
        description=payload.description,
        requires_expiration=payload.requires_expiration,
        default_validity_months=payload.default_validity_months,
        is_active=payload.is_active,
    )

    db.add(qualification)
    db.commit()
    db.refresh(qualification)
    return qualification


@router.put("/{qualification_id}", response_model=QualificationResponse)
def update_qualification(
    qualification_id: uuid.UUID,
    payload: QualificationUpdate,
    db: Session = Depends(get_db),
):
    qualification = db.query(Qualification).filter(Qualification.id == qualification_id).first()
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")

    if payload.organization_id:
        organization = db.query(Organization).filter(Organization.id == payload.organization_id).first()
        if not organization:
            raise HTTPException(status_code=400, detail="Organization not found")

    if payload.code and payload.code != qualification.code:
        existing = db.query(Qualification).filter(Qualification.code == payload.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Qualification code already exists")

    new_requires_expiration = (
        payload.requires_expiration
        if payload.requires_expiration is not None
        else qualification.requires_expiration
    )
    new_default_validity_months = (
        payload.default_validity_months
        if "default_validity_months" in payload.model_dump(exclude_unset=True)
        else qualification.default_validity_months
    )

    if new_requires_expiration and new_default_validity_months is None:
        raise HTTPException(
            status_code=422,
            detail="default_validity_months is required when requires_expiration is true",
        )

    if not new_requires_expiration and new_default_validity_months is not None:
        raise HTTPException(
            status_code=422,
            detail="default_validity_months must be null when requires_expiration is false",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(qualification, field, value)

    db.commit()
    db.refresh(qualification)
    return qualification


@router.delete("/{qualification_id}")
def delete_qualification(qualification_id: uuid.UUID, db: Session = Depends(get_db)):
    qualification = db.query(Qualification).filter(Qualification.id == qualification_id).first()
    if not qualification:
        raise HTTPException(status_code=404, detail="Qualification not found")

    db.delete(qualification)
    db.commit()
    return {"message": "Qualification deleted successfully"}