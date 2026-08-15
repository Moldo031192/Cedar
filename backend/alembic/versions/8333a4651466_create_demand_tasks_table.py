from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "8333a4651466"
down_revision = "3bc06cbcc627"
branch_labels = None
depends_on = None


demand_task_type_enum = sa.Enum(
    "DEBOARDING",
    "BOARDING",
    "TURNAROUND",
    name="demand_task_type_enum",
)

demand_task_status_enum = sa.Enum(
    "PLANNED",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
    name="demand_task_status_enum",
)


def upgrade() -> None:
    demand_task_type_enum.create(op.get_bind(), checkfirst=True)
    demand_task_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "demand_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flight_reference", sa.String(length=100), nullable=False),
        sa.Column("task_type", demand_task_type_enum, nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("target_headcount", sa.Integer(), nullable=False),
        sa.Column("minimum_headcount", sa.Integer(), nullable=False),
        sa.Column("airline_contract_reference", sa.String(length=255), nullable=True),
        sa.Column("status", demand_task_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_demand_tasks_organization_id"), "demand_tasks", ["organization_id"], unique=False)
    op.create_index(op.f("ix_demand_tasks_flight_reference"), "demand_tasks", ["flight_reference"], unique=False)

    op.create_table(
        "demand_task_qualifications",
        sa.Column("demand_task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("qualification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["demand_task_id"], ["demand_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["qualification_id"], ["qualifications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("demand_task_id", "qualification_id"),
    )


def downgrade() -> None:
    op.drop_table("demand_task_qualifications")

    op.drop_index(op.f("ix_demand_tasks_flight_reference"), table_name="demand_tasks")
    op.drop_index(op.f("ix_demand_tasks_organization_id"), table_name="demand_tasks")
    op.drop_table("demand_tasks")

    demand_task_status_enum.drop(op.get_bind(), checkfirst=True)
    demand_task_type_enum.drop(op.get_bind(), checkfirst=True)
