import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.shift import Shift
from app.models.organization import Organization
from app.schemas.shift import ShiftCreate, ShiftUpdate, ShiftResponse

router = APIRouter(prefix="/shifts", tags=["Shifts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _validate_time_semantics(start_time, end_time, crosses_midnight):
    if start_time == end_time:
        raise HTTPException(status_code=400, detail="start_time and end_time cannot be equal")
    if crosses_midnight:
        if start_time <= end_time:
            raise HTTPException(
                status_code=400,
                detail="when crosses_midnight is true, start_time must be greater than end_time",
            )
    else:
        if start_time >= end_time:
            raise HTTPException(
                status_code=400,
                detail="when crosses_midnight is false, start_time must be less than end_time",
            )


@router.get("", response_model=list[ShiftResponse])
def list_shifts(db: Session = Depends(get_db)):
    return db.query(Shift).order_by(Shift.created_at.desc()).all()


@router.get("/{shift_id}", response_model=ShiftResponse)
def get_shift(shift_id: uuid.UUID, db: Session = Depends(get_db)):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    return shift


@router.post("", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
def create_shift(payload: ShiftCreate, db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == payload.organization_id).first()
    if not organization:
        raise HTTPException(status_code=400, detail="Organization not found")

    existing = (
        db.query(Shift)
        .filter(Shift.organization_id == payload.organization_id, Shift.code == payload.code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Shift code already exists for this organization")

    shift = Shift(
        organization_id=payload.organization_id,
        name=payload.name,
        code=payload.code,
        start_time=payload.start_time,
        end_time=payload.end_time,
        crosses_midnight=payload.crosses_midnight,
        target_headcount=payload.target_headcount,
        support_headcount=payload.support_headcount,
        is_active=payload.is_active,
    )

    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


@router.put("/{shift_id}", response_model=ShiftResponse)
def update_shift(shift_id: uuid.UUID, payload: ShiftUpdate, db: Session = Depends(get_db)):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    if payload.organization_id:
        organization = db.query(Organization).filter(Organization.id == payload.organization_id).first()
        if not organization:
            raise HTTPException(status_code=400, detail="Organization not found")

    new_organization_id = payload.organization_id if payload.organization_id is not None else shift.organization_id
    new_code = payload.code if payload.code is not None else shift.code

    if new_organization_id != shift.organization_id or new_code != shift.code:
        existing = (
            db.query(Shift)
            .filter(
                Shift.organization_id == new_organization_id,
                Shift.code == new_code,
                Shift.id != shift.id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Shift code already exists for this organization")

    new_start_time = payload.start_time if payload.start_time is not None else shift.start_time
    new_end_time = payload.end_time if payload.end_time is not None else shift.end_time
    new_crosses_midnight = (
        payload.crosses_midnight if payload.crosses_midnight is not None else shift.crosses_midnight
    )

    _validate_time_semantics(new_start_time, new_end_time, new_crosses_midnight)

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(shift, field, value)

    db.commit()
    db.refresh(shift)
    return shift


@router.delete("/{shift_id}")
def delete_shift(shift_id: uuid.UUID, db: Session = Depends(get_db)):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    db.delete(shift)
    db.commit()
    return {"message": "Shift deleted successfully"}