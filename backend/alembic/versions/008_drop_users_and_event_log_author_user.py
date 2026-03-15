"""Drop users table and event_logs.author_user_id (single admin via env password)

Revision ID: 008
Revises: 007
Create Date: 2026-03-15

"""
from typing import Sequence, Union
from alembic import op


revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Dropping the column drops the FK to users in PostgreSQL
    op.drop_column("event_logs", "author_user_id")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")


def downgrade() -> None:
    import sqlalchemy as sa
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.add_column(
        "event_logs",
        sa.Column("author_user_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "event_logs_author_user_id_fkey",
        "event_logs",
        "users",
        ["author_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
