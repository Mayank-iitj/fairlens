"""Add LLM bias analysis tables

Revision ID: 0002_llm_bias
Revises: 0001_initial
Create Date: 2026-04-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_llm_bias"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create LLM bias analysis tables."""
    op.create_table(
        "llm_bias_analyses",
        sa.Column("id", sa.String(length=36), nullable=False, primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("text_input", sa.Text(), nullable=False),
        sa.Column("overall_bias_score", sa.Float(), nullable=False),
        sa.Column("bias_level", sa.String(length=32), nullable=False),
        sa.Column("analysis_results", sa.JSON(), nullable=False),
        sa.Column("detected_biases", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("risks", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
    )
    op.create_index("ix_llm_bias_analyses_user_id", "llm_bias_analyses", ["user_id"])
    op.create_index("ix_llm_bias_analyses_created_at", "llm_bias_analyses", ["created_at"])

    op.create_table(
        "llm_bias_detection_metrics",
        sa.Column("id", sa.String(length=36), nullable=False, primary_key=True),
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("algorithm", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["llm_bias_analyses.id"], ),
    )
    op.create_index("ix_llm_bias_detection_metrics_analysis_id", "llm_bias_detection_metrics", ["analysis_id"])


def downgrade() -> None:
    """Drop LLM bias analysis tables."""
    op.drop_index("ix_llm_bias_detection_metrics_analysis_id", table_name="llm_bias_detection_metrics")
    op.drop_table("llm_bias_detection_metrics")
    
    op.drop_index("ix_llm_bias_analyses_created_at", table_name="llm_bias_analyses")
    op.drop_index("ix_llm_bias_analyses_user_id", table_name="llm_bias_analyses")
    op.drop_table("llm_bias_analyses")
