"""add skill table

Revision ID: f1a2b3c4d5e6
Revises: d5e6f7a8b9c0
Create Date: 2026-04-24 12:20:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'd5e6f7a8b9c0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'skill',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('account_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), server_default=sa.text("''::character varying"), nullable=False),
        sa.Column('description', sa.Text(), server_default=sa.text("''::text"), nullable=False),
        sa.Column('content', sa.Text(), server_default=sa.text("''::text"), nullable=False),
        sa.Column('category', sa.String(length=100), server_default=sa.text("''::character varying"), nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP(0)'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP(0)'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_skill_id'),
    )
    with op.batch_alter_table('skill', schema=None) as batch_op:
        batch_op.create_index('idx_skill_account_id', ['account_id'], unique=False)


def downgrade():
    with op.batch_alter_table('skill', schema=None) as batch_op:
        batch_op.drop_index('idx_skill_account_id')

    op.drop_table('skill')
