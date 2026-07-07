"""add authentication controls and security events"""

from alembic import op
import sqlalchemy as sa

revision = "20260707_04"
down_revision = "20260707_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("users", sa.Column("locked_until", sa.DateTime(), nullable=True))
    op.create_table(
        "security_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_ip", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_security_events_event_type", "security_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_security_events_event_type", table_name="security_events")
    op.drop_table("security_events")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
