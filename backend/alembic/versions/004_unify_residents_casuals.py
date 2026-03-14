"""Unify residents and casual_encounters into single residents table

Revision ID: 004
Revises: 003
Create Date: 2026-03-14

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to residents
    op.add_column("residents", sa.Column("full_name", sa.String(200), nullable=True))
    op.add_column("residents", sa.Column("source", sa.String(20), nullable=False, server_default="uploaded"))
    op.add_column(
        "residents",
        sa.Column("created_by_volunteer_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_residents_created_by_volunteer",
        "residents",
        "volunteers",
        ["created_by_volunteer_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # Make first_name, last_name nullable (for casual-only rows)
    op.alter_column(
        "residents",
        "first_name",
        existing_type=sa.String(100),
        nullable=True,
    )
    op.alter_column(
        "residents",
        "last_name",
        existing_type=sa.String(100),
        nullable=True,
    )
    # Migrate casual_encounters into residents
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            INSERT INTO residents (
                event_id, full_name, address, phone, status, volunteer_notes,
                source, created_by_volunteer_id, created_at, updated_at
            )
            SELECT
                event_id, full_name, address, phone, status, notes,
                'casual', created_by_volunteer_id, created_at, updated_at
            FROM casual_encounters
        """)
    )
    # Drop casual_encounters
    op.drop_index("ix_casual_encounters_id", table_name="casual_encounters")
    op.drop_table("casual_encounters")


def downgrade() -> None:
    # Recreate casual_encounters table
    op.create_table(
        "casual_encounters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("status", sa.Enum("UNCHECKED", "HEALTHY", "INJURED", "EVACUATED", "ABSENT", name="residentstatus"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_volunteer_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_volunteer_id"], ["volunteers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_casual_encounters_id", "casual_encounters", ["id"], unique=False)
    # Migrate back: copy rows with source='casual' into casual_encounters (lose new ids)
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            INSERT INTO casual_encounters (
                event_id, full_name, address, phone, status, notes,
                created_by_volunteer_id, created_at, updated_at
            )
            SELECT
                event_id, full_name, address, phone, status, volunteer_notes,
                created_by_volunteer_id, created_at, updated_at
            FROM residents
            WHERE source = 'casual'
        """)
    )
    # Delete casual rows from residents
    conn.execute(sa.text("DELETE FROM residents WHERE source = 'casual'"))
    # Remove new columns from residents
    op.drop_constraint("fk_residents_created_by_volunteer", "residents", type_="foreignkey")
    op.drop_column("residents", "created_by_volunteer_id")
    op.drop_column("residents", "source")
    op.drop_column("residents", "full_name")
    op.alter_column("residents", "first_name", nullable=False)
    op.alter_column("residents", "last_name", nullable=False)
