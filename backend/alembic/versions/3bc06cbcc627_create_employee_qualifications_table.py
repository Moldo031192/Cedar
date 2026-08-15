from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "3bc06cbcc627"
down_revision = "a14d46e05aea"
branch_labels = None
depends_on = None


employee_qualification_status_enum = sa.Enum(
    "ACTIVE",
    "EXPIRED",
    "SUSPENDED",
    name="employee_qualification_status_enum",
)


def upgrade() -> None:
    employee_qualification_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "employee_qualifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("qualification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("obtained_at", sa.Date(), nullable=False),
        sa.Column("expires_at", sa.Date(), nullable=True),
        sa.Column("status", employee_qualification_status_enum, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["qualification_id"], ["qualifications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_employee_qualifications_employee_id"), "employee_qualifications", ["employee_id"], unique=False)
    op.create_index(op.f("ix_employee_qualifications_qualification_id"), "employee_qualifications", ["qualification_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_employee_qualifications_qualification_id"), table_name="employee_qualifications")
    op.drop_index(op.f("ix_employee_qualifications_employee_id"), table_name="employee_qualifications")
    op.drop_table("employee_qualifications")

    employee_qualification_status_enum.drop(op.get_bind(), checkfirst=True)
