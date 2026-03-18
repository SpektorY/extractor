"""Add volunteer status and volunteer OTP table

Revision ID: 011
Revises: 010
Create Date: 2026-03-17

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    volunteerstatus = sa.Enum("PENDING", "APPROVED", name="volunteerstatus")
    volunteerstatus.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "volunteers",
        sa.Column(
            "status",
            volunteerstatus,
            nullable=True,
            server_default="APPROVED",
        ),
    )
    op.execute("UPDATE volunteers SET status = 'APPROVED' WHERE status IS NULL")
    op.alter_column("volunteers", "status", nullable=False, server_default="PENDING")

    op.create_table(
        "volunteer_otps",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_volunteer_otps_phone", "volunteer_otps", ["phone"])


def downgrade() -> None:
    op.drop_index("ix_volunteer_otps_phone", table_name="volunteer_otps")
    op.drop_table("volunteer_otps")
    op.drop_column("volunteers", "status")
    op.execute("DROP TYPE IF EXISTS volunteerstatus")
