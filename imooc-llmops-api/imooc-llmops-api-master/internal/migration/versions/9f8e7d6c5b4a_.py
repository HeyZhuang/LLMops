"""add skills columns to app config tables

Revision ID: 9f8e7d6c5b4a
Revises: f1a2b3c4d5e6
Create Date: 2026-04-24 15:30:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "9f8e7d6c5b4a"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("app_config", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("skills", JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False)
        )

    with op.batch_alter_table("app_config_version", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("skills", JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False)
        )


def downgrade():
    with op.batch_alter_table("app_config_version", schema=None) as batch_op:
        batch_op.drop_column("skills")

    with op.batch_alter_table("app_config", schema=None) as batch_op:
        batch_op.drop_column("skills")
