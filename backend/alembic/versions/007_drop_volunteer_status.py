"""Drop volunteer status column and enum from volunteers

Revision ID: 007
Revises: 006
Create Date: 2026-03-15

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("volunteers", "status")
    op.execute("DROP TYPE IF EXISTS volunteerstatus")


def downgrade() -> None:
    volunteerstatus = sa.Enum(
        "PENDING", "APPROVED", name="volunteerstatus"
    )
    volunteerstatus.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "volunteers",
        sa.Column(
            "status",
            volunteerstatus,
            nullable=False,
            server_default="APPROVED",
        ),
    )
