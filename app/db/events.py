#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库事件模块

该模块处理数据库连接的生命周期事件，如建立连接、关闭连接等。
用于在应用启动和关闭时自动管理数据库资源。
"""

import logging
from typing import Callable
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.core.config import settings
from app.core.metrics import set_db_connections
from app.db.session import get_db, engine, async_session_maker


async def connect_to_db(app: FastAPI) -> None:
    """
    连接到数据库
    
    在应用启动时建立数据库连接，并将连接对象保存到应用状态中。
    
    参数:
        app: FastAPI应用实例
        
    返回:
        None
    """
    try:
        # 将会话制造工厂添加到应用状态
        app.state.db_session_maker = async_session_maker
        
        # 测试连接
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
            
            # 由于AsyncEngine没有get_engine_status方法，直接设置连接状态
            # 设置当前连接数为1
            set_db_connections(1)
        
        logging.info("数据库连接成功")
    except Exception as e:
        logging.error(f"数据库连接失败: {e}")
        raise


async def close_db_connection(app: FastAPI) -> None:
    """
    关闭数据库连接
    
    在应用关闭时释放数据库连接资源。
    
    参数:
        app: FastAPI应用实例
        
    返回:
        None
    """
    try:
        await engine.dispose()
        # 将连接数设置为0
        set_db_connections(0)
        logging.info("数据库连接已关闭")
    except Exception as e:
        logging.error(f"关闭数据库连接时出错: {e}")
        raise 