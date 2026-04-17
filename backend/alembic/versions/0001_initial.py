"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-16 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("plan", sa.String(length=50), nullable=False),
        sa.Column("settings_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("org_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "datasets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("schema_json", sa.JSON(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "audits",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("dataset_id", sa.String(length=36), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("model_path", sa.String(length=512), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "audit_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("audit_id", sa.String(length=36), sa.ForeignKey("audits.id"), nullable=False),
        sa.Column("metric_name", sa.String(length=128), nullable=False),
        sa.Column("group_name", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_audit_results_audit_id", "audit_results", ["audit_id"], unique=False)
    op.create_table(
        "remediations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("audit_id", sa.String(length=36), sa.ForeignKey("audits.id"), nullable=False),
        sa.Column("strategy", sa.String(length=128), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("before_metrics", sa.JSON(), nullable=False),
        sa.Column("after_metrics", sa.JSON(), nullable=False),
    )
    op.create_table(
        "reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("audit_id", sa.String(length=36), sa.ForeignKey("audits.id"), nullable=False),
        sa.Column("pdf_path", sa.String(length=512), nullable=True),
        sa.Column("summary_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_unique_constraint("uq_reports_audit_id", "reports", ["audit_id"])
    op.create_table(
        "monitors",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("audit_id", sa.String(length=36), sa.ForeignKey("audits.id"), nullable=False),
        sa.Column("schedule_cron", sa.String(length=64), nullable=False),
        sa.Column("alert_config", sa.JSON(), nullable=False),
        sa.Column("last_run", sa.DateTime(), nullable=True),
        sa.Column("next_run", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("monitor_id", sa.String(length=36), sa.ForeignKey("monitors.id"), nullable=False),
        sa.Column("triggered_at", sa.DateTime(), nullable=False),
        sa.Column("metric", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("notified", sa.Boolean(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("monitors")
    op.drop_constraint("uq_reports_audit_id", "reports", type_="unique")
    op.drop_table("reports")
    op.drop_table("remediations")
    op.drop_index("ix_audit_results_audit_id", table_name="audit_results")
    op.drop_table("audit_results")
    op.drop_table("audits")
    op.drop_table("datasets")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("organizations")
