"""Add event archiving and volunteer attendance status

Revision ID: 009
Revises: 008
Create Date: 2026-03-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("events", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))

    volunteereventstatus = sa.Enum(
        "COMING",
        "NOT_COMING",
        "ARRIVED",
        "LEFT",
        name="volunteereventstatus",
    )
    volunteereventstatus.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "event_volunteers",
        sa.Column("status", volunteereventstatus, nullable=True),
    )
    op.execute("UPDATE event_volunteers SET status = 'ARRIVED' WHERE status IS NULL")


def downgrade() -> None:
    op.drop_column("event_volunteers", "status")
    op.execute("DROP TYPE IF EXISTS volunteereventstatus")
    op.drop_column("events", "archived_at")
