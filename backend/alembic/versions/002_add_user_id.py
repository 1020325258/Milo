"""添加 user_id 字段实现用户隔离

Revision ID: 002
Revises: 001
Create Date: 2026-06-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # knowledge_base 表添加 user_id 列
    op.add_column(
        'knowledge_base',
        sa.Column('user_id', sa.String(length=100), nullable=False, server_default='default'),
    )
    op.create_index('ix_knowledge_base_user_id', 'knowledge_base', ['user_id'])

    # 删除旧的 name 唯一约束，添加 (name, user_id) 联合唯一约束
    op.drop_index('ix_knowledge_base_name', table_name='knowledge_base')
    op.create_index('ix_knowledge_base_name', 'knowledge_base', ['name'])
    op.create_unique_constraint(
        'uq_knowledge_base_name_user',
        'knowledge_base',
        ['name', 'user_id'],
    )

    # conversation 表添加 user_id 列
    op.add_column(
        'conversation',
        sa.Column('user_id', sa.String(length=100), nullable=False, server_default='default'),
    )
    op.create_index('ix_conversation_user_id', 'conversation', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_conversation_user_id', table_name='conversation')
    op.drop_column('conversation', 'user_id')

    op.drop_constraint('uq_knowledge_base_name_user', 'knowledge_base', type_='unique')
    op.drop_index('ix_knowledge_base_user_id', table_name='knowledge_base')
    op.drop_column('knowledge_base', 'user_id')
