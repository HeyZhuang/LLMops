"""create message_feedback table

Revision ID: c4d5e6f7a8b9
Revises: b3f5a8c61d42
Create Date: 2026-03-18 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c4d5e6f7a8b9'
down_revision = 'b3f5a8c61d42'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'message_feedback',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('app_id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('message_id', sa.UUID(), nullable=False),
        sa.Column('rating', sa.String(20), nullable=False, server_default=sa.text("''::character varying")),
        sa.Column('content', sa.Text(), nullable=False, server_default=sa.text("''::text")),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP(0)')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP(0)')),
        sa.PrimaryKeyConstraint('id', name='pk_message_feedback_id'),
    )
    # 添加索引以加速查询
    op.create_index('idx_message_feedback_message_id', 'message_feedback', ['message_id'])
    op.create_index('idx_message_feedback_app_id', 'message_feedback', ['app_id'])


def downgrade():
    op.drop_index('idx_message_feedback_app_id', table_name='message_feedback')
    op.drop_index('idx_message_feedback_message_id', table_name='message_feedback')
    op.drop_table('message_feedback')
