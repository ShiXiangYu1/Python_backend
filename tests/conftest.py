#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试配置模块

提供测试所需的固定装置和公共设施，如数据库会话、测试客户端等。
使用pytest的fixture机制组织和共享测试资源。
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.base import BaseModel
from app.db.session import get_db
from app.main import create_application


# 使用测试数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# 创建测试引擎和会话
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    
    yield engine
    
    # 删除所有表
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # 开始事务
        async with session.begin():
            yield session
        # 回滚事务，保持测试隔离
        await session.rollback()


@pytest.fixture
def app(db_session) -> FastAPI:
    """创建测试应用"""
    app = create_application()
    
    # 重写依赖项，使用测试数据库会话
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    return app


@pytest.fixture
def client(app) -> Generator:
    """创建测试客户端"""
    with TestClient(app) as c:
        yield c 