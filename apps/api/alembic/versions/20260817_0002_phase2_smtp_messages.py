"""phase 2 smtp messages

Revision ID: 20260817_0002
Revises: 20260817_0001
Create Date: 2026-08-17 00:30:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260817_0002"
down_revision = "20260817_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "smtp_providers",
        sa.Column("use_ssl", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "smtp_providers",
        sa.Column(
            "throttle_limit_per_minute", sa.Integer(), nullable=False, server_default="60"
        ),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "provider_id", sa.Integer(), sa.ForeignKey("smtp_providers.id"), nullable=False
        ),
        sa.Column(
            "sender_identity_id",
            sa.Integer(),
            sa.ForeignKey("sender_identities.id"),
            nullable=False,
        ),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True, unique=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("smtp_providers", "use_ssl", server_default=None)
    op.alter_column("smtp_providers", "throttle_limit_per_minute", server_default=None)


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_column("smtp_providers", "throttle_limit_per_minute")
    op.drop_column("smtp_providers", "use_ssl")
