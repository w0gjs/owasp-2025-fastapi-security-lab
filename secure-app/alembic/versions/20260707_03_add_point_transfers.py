"""add point transfer scenario"""

from alembic import op
import sqlalchemy as sa

revision = "20260707_03"
down_revision = "20260706_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("points", sa.Integer(), nullable=False, server_default="1000"),
    )
    op.create_table(
        "point_transfers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("recipient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("point_transfers")
    op.drop_column("users", "points")
