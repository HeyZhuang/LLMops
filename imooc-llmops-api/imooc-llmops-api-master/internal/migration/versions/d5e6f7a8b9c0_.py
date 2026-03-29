"""create prompt_template table

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-03-18 10:00:01.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd5e6f7a8b9c0'
down_revision = 'c4d5e6f7a8b9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'prompt_template',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('account_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column('description', sa.Text(), nullable=False, server_default=sa.text("''::text")),
        sa.Column('content', sa.Text(), nullable=False, server_default=sa.text("''::text")),
        sa.Column('category', sa.String(100), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP(0)')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP(0)')),
        sa.PrimaryKeyConstraint('id', name='pk_prompt_template_id'),
    )
    op.create_index('idx_prompt_template_account_id', 'prompt_template', ['account_id'])


def downgrade():
    op.drop_index('idx_prompt_template_account_id', table_name='prompt_template')
    op.drop_table('prompt_template')
