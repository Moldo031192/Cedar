from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "f1a9c3d2b7e4"
down_revision = "a14d46e05aea"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "qualifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requires_expiration", sa.Boolean(), nullable=False),
        sa.Column("default_validity_months", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_qualifications_organization_id"), "qualifications", ["organization_id"], unique=False)
    op.create_index(op.f("ix_qualifications_code"), "qualifications", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_qualifications_code"), table_name="qualifications")
    op.drop_index(op.f("ix_qualifications_organization_id"), table_name="qualifications")
    op.drop_table("qualifications")
