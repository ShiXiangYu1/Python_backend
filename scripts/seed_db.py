#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库种子脚本

该脚本用于初始化数据库中的基础数据，如管理员用户、默认配置等。
在首次设置应用程序或重置数据库后运行。
"""

import asyncio
import logging
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.security import create_password_hash
from app.db.session import async_session_maker
from app.models.user import User, UserRole


async def seed_admin_user(session: AsyncSession) -> None:
    """
    创建管理员用户
    
    检查是否已存在管理员用户，如果不存在则创建一个。
    
    参数:
        session: 数据库会话
        
    返回:
        None
    """
    # 检查是否已存在管理员用户
    result = await session.execute(
        select(User).filter(User.role == UserRole.ADMIN)
    )
    admin_user = result.scalars().first()
    
    if admin_user:
        logging.info("管理员用户已存在，跳过创建")
        return
    
    # 创建管理员用户
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=create_password_hash("Admin@12345"),
        full_name="系统管理员",
        is_active=True,
        role=UserRole.ADMIN
    )
    
    session.add(admin_user)
    await session.commit()
    logging.info("成功创建管理员用户")


async def seed_default_data(session: AsyncSession) -> None:
    """
    填充默认数据
    
    包括创建管理员用户、示例模型等。
    
    参数:
        session: 数据库会话
        
    返回:
        None
    """
    # 创建管理员用户
    await seed_admin_user(session)
    
    # TODO: 添加更多默认数据，如示例模型、常用配置等


async def main() -> None:
    """
    主函数
    
    初始化日志，创建数据库会话，并运行种子数据填充函数。
    
    返回:
        None
    """
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    logging.info("开始填充数据库种子数据...")
    
    # 创建会话
    async with async_session_maker() as session:
        await seed_default_data(session)
    
    logging.info("数据库种子数据填充完成")


if __name__ == "__main__":
    asyncio.run(main()) 