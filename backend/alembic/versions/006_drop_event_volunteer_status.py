"""Drop volunteer status column and enum from event_volunteers

Revision ID: 006
Revises: 005
Create Date: 2026-03-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("event_volunteers", "status")
    op.execute("DROP TYPE IF EXISTS volunteereventstatus")


def downgrade() -> None:
    volunteereventstatus = sa.Enum(
        "PENDING", "COMING", "NOT_COMING", "ARRIVED", name="volunteereventstatus"
    )
    volunteereventstatus.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "event_volunteers",
        sa.Column(
            "status",
            volunteereventstatus,
            nullable=False,
            server_default="PENDING",
        ),
    )
