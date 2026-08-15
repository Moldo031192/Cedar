import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.demand_task import DemandTask
from app.models.organization import Organization
from app.models.qualification import Qualification
from app.schemas.demand_task import (
    DemandTaskCreate,
    DemandTaskUpdate,
    DemandTaskResponse,
)

router = APIRouter(prefix="/demand-tasks", tags=["DemandTasks"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _resolve_qualifications(db: Session, qualification_ids: list[uuid.UUID]) -> list[Qualification]:
    if not qualification_ids:
        return []

    qualifications = db.query(Qualification).filter(Qualification.id.in_(qualification_ids)).all()

    found_ids = {q.id for q in qualifications}
    missing_ids = set(qualification_ids) - found_ids
    if missing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Qualification(s) not found: {', '.join(str(i) for i in missing_ids)}",
        )

    return qualifications


@router.get("", response_model=list[DemandTaskResponse])
def list_demand_tasks(db: Session = Depends(get_db)):
    return db.query(DemandTask).order_by(DemandTask.start_time.desc()).all()


@router.get("/{demand_task_id}", response_model=DemandTaskResponse)
def get_demand_task(demand_task_id: uuid.UUID, db: Session = Depends(get_db)):
    demand_task = db.query(DemandTask).filter(DemandTask.id == demand_task_id).first()
    if not demand_task:
        raise HTTPException(status_code=404, detail="Demand task not found")
    return demand_task


@router.post("", response_model=DemandTaskResponse, status_code=status.HTTP_201_CREATED)
def create_demand_task(payload: DemandTaskCreate, db: Session = Depends(get_db)):
    organization = db.query(Organization).filter(Organization.id == payload.organization_id).first()
    if not organization:
        raise HTTPException(status_code=400, detail="Organization not found")

    qualifications = _resolve_qualifications(db, payload.required_qualification_ids)

    demand_task = DemandTask(
        organization_id=payload.organization_id,
        flight_reference=payload.flight_reference,
        task_type=payload.task_type,
        start_time=payload.start_time,
        duration_minutes=payload.duration_minutes,
        target_headcount=payload.target_headcount,
        minimum_headcount=payload.minimum_headcount,
        airline_contract_reference=payload.airline_contract_reference,
        status=payload.status,
    )
    demand_task.required_qualifications = qualifications

    db.add(demand_task)
    db.commit()
    db.refresh(demand_task)
    return demand_task


@router.put("/{demand_task_id}", response_model=DemandTaskResponse)
def update_demand_task(
    demand_task_id: uuid.UUID,
    payload: DemandTaskUpdate,
    db: Session = Depends(get_db),
):
    demand_task = db.query(DemandTask).filter(DemandTask.id == demand_task_id).first()
    if not demand_task:
        raise HTTPException(status_code=404, detail="Demand task not found")

    if payload.organization_id:
        organization = db.query(Organization).filter(Organization.id == payload.organization_id).first()
        if not organization:
            raise HTTPException(status_code=400, detail="Organization not found")

    new_minimum = (
        payload.minimum_headcount if payload.minimum_headcount is not None else demand_task.minimum_headcount
    )
    new_target = (
        payload.target_headcount if payload.target_headcount is not None else demand_task.target_headcount
    )
    if new_minimum > new_target:
        raise HTTPException(
            status_code=400,
            detail="minimum_headcount cannot be greater than target_headcount",
        )

    if payload.duration_minutes is not None and payload.duration_minutes <= 0:
        raise HTTPException(status_code=400, detail="duration_minutes must be greater than zero")

    update_data = payload.model_dump(exclude_unset=True, exclude={"required_qualification_ids"})

    for field, value in update_data.items():
        setattr(demand_task, field, value)

    if payload.required_qualification_ids is not None:
        demand_task.required_qualifications = _resolve_qualifications(db, payload.required_qualification_ids)

    db.commit()
    db.refresh(demand_task)
    return demand_task


@router.delete("/{demand_task_id}")
def delete_demand_task(demand_task_id: uuid.UUID, db: Session = Depends(get_db)):
    demand_task = db.query(DemandTask).filter(DemandTask.id == demand_task_id).first()
    if not demand_task:
        raise HTTPException(status_code=404, detail="Demand task not found")

    db.delete(demand_task)
    db.commit()
    return {"message": "Demand task deleted successfully"}
