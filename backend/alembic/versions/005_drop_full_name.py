"""Drop redundant full_name from residents; use first_name/last_name only

Revision ID: 005
Revises: 004
Create Date: 2026-03-14

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migrate full_name into first_name where we'd lose data (e.g. casual rows)
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE residents
            SET first_name = COALESCE(full_name, first_name)
            WHERE full_name IS NOT NULL AND (first_name IS NULL OR first_name = '')
        """)
    )
    op.drop_column("residents", "full_name")


def downgrade() -> None:
    op.add_column("residents", sa.Column("full_name", sa.String(200), nullable=True))
