"""add multi_agent_config column to app_config and app_config_version

Revision ID: b3f5a8c61d42
Revises: 775e752e0220
Create Date: 2026-03-17 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'b3f5a8c61d42'
down_revision = '775e752e0220'
branch_labels = None
depends_on = None


def upgrade():
    # Add multi_agent_config column to app_config
    op.add_column('app_config', sa.Column(
        'multi_agent_config',
        JSONB(),
        nullable=False,
        server_default=sa.text("'{}'::jsonb"),
    ))

    # Add multi_agent_config column to app_config_version
    op.add_column('app_config_version', sa.Column(
        'multi_agent_config',
        JSONB(),
        nullable=False,
        server_default=sa.text("'{}'::jsonb"),
    ))


def downgrade():
    op.drop_column('app_config_version', 'multi_agent_config')
    op.drop_column('app_config', 'multi_agent_config')
