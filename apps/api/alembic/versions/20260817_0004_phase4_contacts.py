"""phase 4 contacts lists suppression import

Revision ID: 20260817_0004
Revises: 20260817_0003
Create Date: 2026-08-17 12:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "20260817_0004"
down_revision = "20260817_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), unique=True, nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=True),
        sa.Column("last_name", sa.String(length=120), nullable=True),
        sa.Column("custom_fields", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_contacts_email", "contacts", ["email"], unique=True)

    op.create_table(
        "contact_lists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "contact_list_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "contact_list_id",
            sa.Integer(),
            sa.ForeignKey("contact_lists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "contact_id",
            sa.Integer(),
            sa.ForeignKey("contacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("contact_list_id", "contact_id", name="uq_list_member"),
    )

    op.create_table(
        "suppression_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), unique=True, nullable=False),
        sa.Column("reason", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_suppression_entries_email", "suppression_entries", ["email"], unique=True)

    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_report", sa.JSON(), nullable=True),
        sa.Column(
            "contact_list_id",
            sa.Integer(),
            sa.ForeignKey("contact_lists.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("csv_data", sa.Text(), nullable=True),
        sa.Column("column_mapping", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("import_jobs")
    op.drop_index("ix_suppression_entries_email", table_name="suppression_entries")
    op.drop_table("suppression_entries")
    op.drop_table("contact_list_members")
    op.drop_table("contact_lists")
    op.drop_index("ix_contacts_email", table_name="contacts")
    op.drop_table("contacts")
