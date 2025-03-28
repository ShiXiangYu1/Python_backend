"""初始数据库结构

Revision ID: 1704c855c7ce
Revises: 
Create Date: 2025-03-25 17:20:56.445871

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = '1704c855c7ce'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### 创建用户表 ###
    op.create_table('user',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=128), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'USER', name='userrole'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)

    # ### 创建API密钥表 ###
    op.create_table('api_key',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('key_prefix', sa.String(length=10), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_key_id'), 'api_key', ['id'], unique=False)
    op.create_index(op.f('ix_api_key_key_prefix'), 'api_key', ['key_prefix'], unique=False)

    # ### 创建模型表 ###
    op.create_table('model',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('framework', sa.Enum('TENSORFLOW', 'PYTORCH', 'ONNX', 'SKLEARN', 'CUSTOM', name='modelframework'), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_hash', sa.String(length=64), nullable=True),
        sa.Column('status', sa.Enum('UPLOADING', 'UPLOADED', 'VALIDATING', 'VALID', 'INVALID', 'DEPLOYING', 'DEPLOYED', 'UNDEPLOYED', 'ARCHIVED', name='modelstatus'), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('endpoint_url', sa.String(length=255), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('latency', sa.Float(), nullable=True),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_id'), 'model', ['id'], unique=False)
    op.create_index(op.f('ix_model_name'), 'model', ['name'], unique=False)

    # ### 创建模型版本表 ###
    op.create_table('model_version',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('change_log', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=255), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_hash', sa.String(length=64), nullable=True),
        sa.Column('status', sa.Enum('UPLOADING', 'UPLOADED', 'VALIDATING', 'VALID', 'INVALID', 'DEPLOYING', 'DEPLOYED', 'UNDEPLOYED', 'ARCHIVED', name='modelstatus'), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.Column('parent_model_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['parent_model_id'], ['model.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_version_id'), 'model_version', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### 删除所有表（按反向顺序） ###
    op.drop_index(op.f('ix_model_version_id'), table_name='model_version')
    op.drop_table('model_version')
    
    op.drop_index(op.f('ix_model_name'), table_name='model')
    op.drop_index(op.f('ix_model_id'), table_name='model')
    op.drop_table('model')
    
    op.drop_index(op.f('ix_api_key_key_prefix'), table_name='api_key')
    op.drop_index(op.f('ix_api_key_id'), table_name='api_key')
    op.drop_table('api_key')
    
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    
    # 删除枚举类型
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='modelframework').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='modelstatus').drop(op.get_bind(), checkfirst=True)
    # ### end Alembic commands ###
