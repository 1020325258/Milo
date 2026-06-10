"""知识库改为共享，移除 user_id

Revision ID: 003
Revises: 002
Create Date: 2026-06-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 尝试删除联合唯一约束（如果存在）
    try:
        op.drop_constraint('uq_knowledge_base_name_user', 'knowledge_base', type_='unique')
    except Exception:
        pass

    # 去重：保留每个 name 下 id 最小的记录，删除其余
    conn.execute(
        sa.text("""
            DELETE k1 FROM knowledge_base k1
            INNER JOIN knowledge_base k2
            ON k1.name = k2.name AND k1.id > k2.id
        """)
    )

    # 删除 user_id 索引和列（如果存在）
    try:
        op.drop_index('ix_knowledge_base_user_id', table_name='knowledge_base')
    except Exception:
        pass
    try:
        op.drop_column('knowledge_base', 'user_id')
    except Exception:
        pass

    # 恢复 name 的唯一约束（如果不存在）
    try:
        op.create_unique_constraint(None, 'knowledge_base', ['name'])
    except Exception:
        pass


def downgrade() -> None:
    op.drop_constraint('knowledge_base_name_key', 'knowledge_base', type_='unique')
    op.add_column(
        'knowledge_base',
        sa.Column('user_id', sa.String(length=100), nullable=False, server_default='default'),
    )
    op.create_index('ix_knowledge_base_user_id', 'knowledge_base', ['user_id'])
    op.create_unique_constraint(
        'uq_knowledge_base_name_user',
        'knowledge_base',
        ['name', 'user_id'],
    )
