import uuid
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SqlEnum, Table, Column, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DemandTaskType(str, Enum):
    DEBOARDING = "DEBOARDING"
    BOARDING = "BOARDING"
    TURNAROUND = "TURNAROUND"


class DemandTaskStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# Tabel de asociere many-to-many: un task poate cere mai multe qualifications,
# o qualification poate fi ceruta de mai multe task-uri.
demand_task_qualifications = Table(
    "demand_task_qualifications",
    Base.metadata,
    Column(
        "demand_task_id",
        UUID(as_uuid=True),
        ForeignKey("demand_tasks.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "qualification_id",
        UUID(as_uuid=True),
        ForeignKey("qualifications.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class DemandTask(Base):
    __tablename__ = "demand_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    flight_reference: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    task_type: Mapped[DemandTaskType] = mapped_column(
        SqlEnum(DemandTaskType, name="demand_task_type_enum"),
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Durata NU este hardcodata in algoritm - vine din request, configurata
    # per airline/contract la nivelul apelantului (viitor profil de contract).
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    target_headcount: Mapped[int] = mapped_column(Integer, nullable=False)
    minimum_headcount: Mapped[int] = mapped_column(Integer, nullable=False)
    # Referinta simpla (Varianta A) - fara FK catre un modul AirlineContract,
    # care va fi decis intr-un sprint ulterior.
    airline_contract_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[DemandTaskStatus] = mapped_column(
        SqlEnum(DemandTaskStatus, name="demand_task_status_enum"),
        nullable=False,
        default=DemandTaskStatus.PLANNED,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    organization = relationship("Organization", back_populates="demand_tasks")
    required_qualifications = relationship(
        "Qualification",
        secondary=demand_task_qualifications,
        lazy="selectin",
    )

    @hybrid_property
    def end_time(self) -> datetime:
        """Calculat din start_time + duration_minutes - nu e coloana separata,
        ca sa nu existe doua surse de adevar pentru acelasi interval."""
        return self.start_time + timedelta(minutes=self.duration_minutes)

    @property
    def required_qualification_ids(self) -> list[uuid.UUID]:
        return [q.id for q in self.required_qualifications]
