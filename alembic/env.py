from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到Python路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# 加载环境变量
load_dotenv(os.path.join(BASE_DIR, ".env"))

try:
    # 导入模型基类和所有模型（用于自动检测变更）
    from app.db.base_class import BaseModel
    
    # 显式导入所有模型以确保它们在元数据中注册
    from app.models.user import User, UserRole
    from app.models.api_key import APIKey
    from app.models.model import Model, ModelVersion, ModelFramework, ModelStatus
    
    target_metadata = BaseModel.metadata
except ImportError:
    # 如果导入失败，使用空元数据
    from sqlalchemy import MetaData
    target_metadata = MetaData()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 设置数据库URL
# 尝试从环境变量获取数据库URL，如果不存在则使用alembic.ini中的配置
database_url = os.getenv("DATABASE_URL")
if database_url:
    # 替换alembic.ini中的配置
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
