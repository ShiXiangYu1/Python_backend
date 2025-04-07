#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库会话模块

该模块管理SQLAlchemy的数据库会话，提供会话创建和依赖注入功能。
支持同步和异步操作方式，适用于不同的使用场景。
"""

from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from app.core.config import settings


# 创建SQLAlchemy基类
Base = declarative_base()

# 根据配置创建异步数据库引擎
# 获取数据库连接URL
engine_url = settings.SQLALCHEMY_DATABASE_URI
# 仅对MySQL连接进行驱动替换，确保支持异步操作
if 'mysql' in engine_url and 'pymysql' in engine_url:
    engine_url = engine_url.replace('pymysql', 'aiomysql')

# 创建异步引擎
engine = create_async_engine(
    engine_url,
    echo=settings.APP_DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 创建异步会话工厂
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 同步引擎（用于迁移等工具）
sync_engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.APP_DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 同步会话工厂
sync_session_maker = sessionmaker(
    sync_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    提供异步数据库会话
    
    创建一个异步会话，用于处理数据库操作，并在操作完成后自动关闭。
    主要用作FastAPI的依赖项。
    
    返回:
        AsyncGenerator[AsyncSession, None]: 异步数据库会话生成器
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db() -> Generator[Session, None, None]:
    """
    提供同步数据库会话
    
    创建一个同步会话，用于处理需要同步执行的数据库操作，如CLI命令等。
    
    返回:
        Generator[Session, None, None]: 同步数据库会话生成器
    """
    with sync_session_maker() as session:
        try:
            yield session
        finally:
            session.close()


async def create_db_and_tables() -> None:
    """
    创建数据库表
    
    在应用启动时根据SQLAlchemy模型创建数据库表。
    如果表已存在，则不会执行任何操作。
    
    此函数适用于开发环境和简单部署。
    对于生产环境，推荐使用数据库迁移工具（如Alembic）。
    """
    import logging
    from sqlalchemy.schema import CreateTable
    
    try:
        # 确保导入所有模型以注册到元数据
        import app.models.user
        import app.models.api_key
        import app.models.model
        import app.models.task
        
        # 创建所有表
        logging.info("创建数据库表...")
        async with engine.begin() as conn:
            # 检查是否为SQLite数据库
            dialect = engine.dialect.name
            if dialect == 'sqlite':
                # SQLite特殊处理：启用外键约束
                from sqlalchemy import text
                await conn.execute(text("PRAGMA foreign_keys=ON"))
            
            # 使用显式的表创建顺序，避免外键依赖性问题
            # 1. 创建不依赖其他表的基础表（users, models）
            from app.models.user import User
            from app.models.model import Model
            
            # 首先创建用户表
            await conn.run_sync(lambda conn: User.__table__.create(conn, checkfirst=True))
            logging.info("创建表: users")
            
            # 然后创建模型表
            await conn.run_sync(lambda conn: Model.__table__.create(conn, checkfirst=True))
            logging.info("创建表: models")
            
            # 2. 创建依赖于基础表的其他表（api_keys, tasks, model_versions等）
            from app.models.api_key import APIKey
            from app.models.task import Task
            from app.models.model import ModelVersion
            
            await conn.run_sync(lambda conn: APIKey.__table__.create(conn, checkfirst=True))
            logging.info("创建表: api_keys")
            
            await conn.run_sync(lambda conn: Task.__table__.create(conn, checkfirst=True))
            logging.info("创建表: tasks")
            
            await conn.run_sync(lambda conn: ModelVersion.__table__.create(conn, checkfirst=True))
            logging.info("创建表: model_versions")
            
            # 3. 创建其他剩余表（如果有）
            # 获取已创建的表
            created_tables = {
                User.__tablename__, Model.__tablename__, 
                APIKey.__tablename__, Task.__tablename__, ModelVersion.__tablename__
            }
            
            # 创建剩余表
            for table in Base.metadata.sorted_tables:
                if table.name not in created_tables:
                    await conn.run_sync(lambda conn, t=table: t.create(conn, checkfirst=True))
                    logging.info(f"创建表: {table.name}")
        
        logging.info("数据库表创建成功")
    except Exception as e:
        logging.error(f"创建数据库表失败: {str(e)}")
        # 在开发环境下重新抛出异常，以便更好地调试
        if settings.APP_DEBUG:
            raise 