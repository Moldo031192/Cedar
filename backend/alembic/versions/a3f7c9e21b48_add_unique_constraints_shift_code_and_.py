"""add unique constraints for shift code and employee shift work date

Revision ID: a3f7c9e21b48
Revises: 913038ade754
Create Date: 2026-08-17 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "a3f7c9e21b48"
down_revision = "913038ade754"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_shifts_organization_id_code", "shifts", ["organization_id", "code"]
    )
    op.create_unique_constraint(
        "uq_employee_shifts_employee_id_work_date",
        "employee_shifts",
        ["employee_id", "work_date"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_employee_shifts_employee_id_work_date", "employee_shifts", type_="unique"
    )
    op.drop_constraint("uq_shifts_organization_id_code", "shifts", type_="unique")