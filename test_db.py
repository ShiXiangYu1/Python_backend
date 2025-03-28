#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库连接测试

测试异步SQLite连接是否能正常工作，用于验证配置。
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 获取当前目录和数据库URL
current_dir = os.getcwd()
db_path = os.path.join(current_dir, "app.db")
DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

print(f"测试数据库连接: {DATABASE_URL}")

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 打印SQL语句
    future=True,
)

# 创建异步会话
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def test_connection():
    """测试数据库连接"""
    async with engine.begin() as conn:
        print("连接成功!")
        # 检查是否存在表
        tables = await conn.run_sync(lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn))
        print(f"表数量: {len(tables)}")
        if tables:
            print("现有表:")
            for table in tables:
                print(f"  - {table}")
        else:
            print("数据库中没有表")

async def main():
    """主函数"""
    try:
        await test_connection()
    except Exception as e:
        print(f"连接错误: {e}")
    finally:
        # 关闭引擎
        await engine.dispose()
        print("引擎已关闭")

if __name__ == "__main__":
    asyncio.run(main()) 