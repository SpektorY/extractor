"""Add resident fields for Excel template

Revision ID: 010
Revises: 009
Create Date: 2026-03-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("residents", sa.Column("identity_number", sa.String(length=20), nullable=True))
    op.add_column("residents", sa.Column("gender", sa.String(length=20), nullable=True))
    op.add_column("residents", sa.Column("city", sa.String(length=100), nullable=True))
    op.add_column("residents", sa.Column("street", sa.String(length=255), nullable=True))
    op.add_column("residents", sa.Column("house_number", sa.String(length=20), nullable=True))
    op.add_column("residents", sa.Column("apartment", sa.String(length=20), nullable=True))
    op.add_column("residents", sa.Column("age", sa.Integer(), nullable=True))
    op.add_column("residents", sa.Column("home_phone", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("residents", "home_phone")
    op.drop_column("residents", "age")
    op.drop_column("residents", "apartment")
    op.drop_column("residents", "house_number")
    op.drop_column("residents", "street")
    op.drop_column("residents", "city")
    op.drop_column("residents", "gender")
    op.drop_column("residents", "identity_number")
