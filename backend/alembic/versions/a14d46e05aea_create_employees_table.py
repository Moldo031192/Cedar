from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "a14d46e05aea"
down_revision = "91fa25437e98"
branch_labels = None
depends_on = None


employment_type_enum = sa.Enum(
    "FULL_TIME",
    "PART_TIME",
    "CONTRACT",
    name="employment_type_enum",
)


def upgrade() -> None:
    employment_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "employees",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_number", sa.String(length=100), nullable=False),
        sa.Column("first_name", sa.String(length=255), nullable=False),
        sa.Column("last_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("employment_type", employment_type_enum, nullable=False),
        sa.Column("hire_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_employees_organization_id"), "employees", ["organization_id"], unique=False)
    op.create_index(op.f("ix_employees_department_id"), "employees", ["department_id"], unique=False)
    op.create_index(op.f("ix_employees_role_id"), "employees", ["role_id"], unique=False)
    op.create_index(op.f("ix_employees_employee_number"), "employees", ["employee_number"], unique=True)
    op.create_index(op.f("ix_employees_email"), "employees", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_employees_email"), table_name="employees")
    op.drop_index(op.f("ix_employees_employee_number"), table_name="employees")
    op.drop_index(op.f("ix_employees_role_id"), table_name="employees")
    op.drop_index(op.f("ix_employees_department_id"), table_name="employees")
    op.drop_index(op.f("ix_employees_organization_id"), table_name="employees")
    op.drop_table("employees")

    employment_type_enum.drop(op.get_bind(), checkfirst=True)
