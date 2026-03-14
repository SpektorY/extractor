"""Drop volunteer_signups table — public and admin both use volunteers table

Revision ID: 002
Revises: 001
Create Date: 2025-03-13

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_volunteer_signups_id"), table_name="volunteer_signups")
    op.drop_table("volunteer_signups")
    op.execute("DROP TYPE IF EXISTS volunteersignupstatus")


def downgrade() -> None:
    op.create_table(
        "volunteer_signups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("area", sa.String(200), nullable=True),
        sa.Column("status", sa.Enum("PENDING", name="volunteersignupstatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_volunteer_signups_id"), "volunteer_signups", ["id"], unique=False)
