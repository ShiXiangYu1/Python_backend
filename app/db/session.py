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