#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简易数据库种子脚本

该脚本使用直接SQL操作向SQLite数据库中添加基础数据，避免复杂的依赖关系。
主要用于创建管理员用户和其他基础数据。
"""

import sqlite3
import uuid
import os
import hashlib
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# 数据库文件路径
DB_PATH = "app.db"


def create_password_hash(password: str) -> str:
    """
    创建密码哈希
    
    使用简单的SHA-256哈希算法（实际应用中应使用更安全的方法如bcrypt）
    
    参数:
        password: 明文密码
        
    返回:
        str: 密码哈希
    """
    return hashlib.sha256(password.encode()).hexdigest()


def seed_admin_user() -> None:
    """
    创建管理员用户
    
    检查是否已存在管理员用户，如果不存在则创建一个。
    
    返回:
        None
    """
    if not os.path.exists(DB_PATH):
        logging.error(f"数据库文件 {DB_PATH} 不存在，请先运行数据库迁移")
        return
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查是否已存在管理员用户
    cursor.execute("SELECT COUNT(*) FROM user WHERE role = 'ADMIN'")
    admin_count = cursor.fetchone()[0]
    
    if admin_count > 0:
        logging.info("管理员用户已存在，跳过创建")
        conn.close()
        return
    
    # 创建管理员用户
    now = datetime.utcnow().isoformat()
    admin_id = str(uuid.uuid4())
    admin_password_hash = create_password_hash("Admin@12345")
    
    cursor.execute(
        """
        INSERT INTO user (
            id, username, email, hashed_password, full_name, is_active, role, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            admin_id,
            "admin",
            "admin@example.com",
            admin_password_hash,
            "系统管理员",
            1,  # is_active=True
            "ADMIN",
            now,
            now
        )
    )
    
    conn.commit()
    conn.close()
    
    logging.info("成功创建管理员用户")
    logging.info("用户名: admin")
    logging.info("密码: Admin@12345")


def main() -> None:
    """
    主函数
    
    运行所有种子数据填充函数。
    
    返回:
        None
    """
    logging.info("开始填充数据库种子数据...")
    
    # 创建管理员用户
    seed_admin_user()
    
    # TODO: 添加更多默认数据
    
    logging.info("数据库种子数据填充完成")


if __name__ == "__main__":
    main() 