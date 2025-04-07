"""添加模型查询性能优化索引

Revision ID: 20250407_161500
Revises: 20250325_172056
Create Date: 2025-04-07 16:15:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '20250407_161500'
down_revision: Union[str, None] = '20250325_172056'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加模型查询性能优化索引"""
    # 获取数据库连接和检测数据库类型
    conn = op.get_bind()
    inspector = inspect(conn)
    dialect_name = conn.dialect.name
    
    # 添加基本索引(所有数据库都支持)
    # 添加 owner_id 索引，优化按所有者筛选查询
    op.create_index(op.f('ix_model_owner_id'), 'model', ['owner_id'], unique=False)
    
    # 添加 is_public 索引，优化公开模型查询
    op.create_index(op.f('ix_model_is_public'), 'model', ['is_public'], unique=False)
    
    # 添加 status 索引，优化模型状态查询
    op.create_index(op.f('ix_model_status'), 'model', ['status'], unique=False)
    
    # 添加 created_at 索引，优化排序
    op.create_index(op.f('ix_model_created_at'), 'model', ['created_at'], unique=False)
    
    # 根据数据库类型添加组合索引
    if dialect_name != 'sqlite':
        # PostgreSQL和MySQL支持复合索引
        # 添加组合索引，优化常见查询
        op.create_index(op.f('ix_model_owner_status'), 'model', ['owner_id', 'status'], unique=False)
        op.create_index(op.f('ix_model_public_status'), 'model', ['is_public', 'status'], unique=False)
    else:
        # SQLite对复合索引支持有限，但我们可以为最常用的查询场景创建一个特殊的索引
        print("SQLite数据库，跳过创建复合索引")


def downgrade() -> None:
    """移除添加的索引"""
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    
    # 对于非SQLite数据库，删除复合索引
    if dialect_name != 'sqlite':
        op.drop_index(op.f('ix_model_public_status'), table_name='model')
        op.drop_index(op.f('ix_model_owner_status'), table_name='model')
    
    # 删除基本索引(所有数据库)
    op.drop_index(op.f('ix_model_created_at'), table_name='model')
    op.drop_index(op.f('ix_model_status'), table_name='model')
    op.drop_index(op.f('ix_model_is_public'), table_name='model')
    op.drop_index(op.f('ix_model_owner_id'), table_name='model') 