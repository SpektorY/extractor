"""Add living_area, status (pending/approved), unique phone to volunteers

Revision ID: 003
Revises: 002
Create Date: 2025-03-13

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add living_area (nullable)
    op.add_column("volunteers", sa.Column("living_area", sa.String(200), nullable=True))
    # Add status enum and column; existing volunteers become APPROVED
    volunteerstatus = sa.Enum("PENDING", "APPROVED", name="volunteerstatus")
    volunteerstatus.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "volunteers",
        sa.Column("status", volunteerstatus, nullable=False, server_default="APPROVED"),
    )
    # Make phone unique (drop existing non-unique index if any, add unique)
    op.drop_index("ix_volunteers_phone", table_name="volunteers")
    op.create_index("ix_volunteers_phone", "volunteers", ["phone"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_volunteers_phone", table_name="volunteers")
    op.create_index("ix_volunteers_phone", "volunteers", ["phone"], unique=False)
    op.drop_column("volunteers", "status")
    op.drop_column("volunteers", "living_area")
    sa.Enum(name="volunteerstatus").drop(op.get_bind(), checkfirst=True)
