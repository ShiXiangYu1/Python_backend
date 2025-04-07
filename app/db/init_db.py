#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简易版数据库初始化脚本

此脚本用于初始化SQLite数据库，创建必要的表并插入示例数据。
不依赖任何第三方库，使用Python标准库sqlite3直接操作数据库。
"""

import os
import sys
import sqlite3
import datetime
import uuid
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent

# 数据库文件路径
DB_PATH = os.path.join(ROOT_DIR, "app.db")

# 表定义SQL
CREATE_TABLES_SQL = {
    "user": """
        CREATE TABLE IF NOT EXISTS user (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            hashed_password TEXT NOT NULL,
            is_active BOOLEAN DEFAULT true,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "model": """
        CREATE TABLE IF NOT EXISTS model (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            framework TEXT,
            version TEXT,
            status TEXT DEFAULT 'pending',
            is_public BOOLEAN DEFAULT false,
            file_path TEXT,
            file_size INTEGER,
            owner_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES user (id)
        );
    """,
    "api_key": """
        CREATE TABLE IF NOT EXISTS api_key (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            key TEXT UNIQUE NOT NULL,
            scopes TEXT,
            is_active BOOLEAN DEFAULT true,
            expires_at TIMESTAMP,
            last_used_at TIMESTAMP,
            usage_count INTEGER DEFAULT 0,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );
    """,
    "model_version": """
        CREATE TABLE IF NOT EXISTS model_version (
            id TEXT PRIMARY KEY,
            version TEXT NOT NULL,
            description TEXT,
            model_id TEXT NOT NULL,
            file_path TEXT,
            file_size INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES model (id)
        );
    """,
    "user_log": """
        CREATE TABLE IF NOT EXISTS user_log (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            action TEXT NOT NULL,
            resource_type TEXT,
            resource_id TEXT,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );
    """,
}

# 插入示例数据SQL
SAMPLE_DATA_SQL = {
    "user": [
        """
        INSERT OR IGNORE INTO user (id, username, email, full_name, hashed_password, is_active, role)
        VALUES (
            '00000000-0000-0000-0000-000000000001',
            'admin',
            'admin@example.com',
            '管理员',
            'hashed_password_here',
            true,
            'admin'
        );
        """,
        """
        INSERT OR IGNORE INTO user (id, username, email, full_name, hashed_password, is_active, role)
        VALUES (
            '00000000-0000-0000-0000-000000000002',
            'user1',
            'user1@example.com',
            '测试用户1',
            'hashed_password_here',
            true,
            'user'
        );
        """,
    ],
    "model": [
        """
        INSERT OR IGNORE INTO model (id, name, description, framework, version, status, is_public, file_path, file_size, owner_id)
        VALUES (
            '00000000-0000-0000-0000-000000000001',
            'BERT-Base',
            'BERT基础模型，用于自然语言处理',
            'PyTorch',
            '1.0.0',
            'active',
            true,
            '/models/bert-base.pt',
            215000000,
            '00000000-0000-0000-0000-000000000001'
        );
        """,
        """
        INSERT OR IGNORE INTO model (id, name, description, framework, version, status, is_public, file_path, file_size, owner_id)
        VALUES (
            '00000000-0000-0000-0000-000000000002',
            'ResNet-50',
            'ResNet-50图像分类模型',
            'TensorFlow',
            '2.0.0',
            'active',
            true,
            '/models/resnet50.h5',
            98000000,
            '00000000-0000-0000-0000-000000000001'
        );
        """,
        """
        INSERT OR IGNORE INTO model (id, name, description, framework, version, status, is_public, file_path, file_size, owner_id)
        VALUES (
            '00000000-0000-0000-0000-000000000003',
            'GPT-2-Small',
            'GPT-2小型语言生成模型',
            'PyTorch',
            '1.0.0',
            'active',
            false,
            '/models/gpt2-small.pt',
            456000000,
            '00000000-0000-0000-0000-000000000002'
        );
        """,
    ],
    "api_key": [
        """
        INSERT OR IGNORE INTO api_key (id, name, key, scopes, is_active, user_id)
        VALUES (
            '00000000-0000-0000-0000-000000000001',
            '管理员API密钥',
            'admin_api_key_123456',
            'read,write,admin',
            true,
            '00000000-0000-0000-0000-000000000001'
        );
        """,
        """
        INSERT OR IGNORE INTO api_key (id, name, key, scopes, is_active, user_id)
        VALUES (
            '00000000-0000-0000-0000-000000000002',
            '只读API密钥',
            'read_only_api_key_123456',
            'read',
            true,
            '00000000-0000-0000-0000-000000000002'
        );
        """,
    ],
    "model_version": [
        """
        INSERT OR IGNORE INTO model_version (id, version, description, model_id, file_path, file_size, status)
        VALUES (
            '00000000-0000-0000-0000-000000000001',
            '1.0.0',
            'BERT初始版本',
            '00000000-0000-0000-0000-000000000001',
            '/models/bert-base-v1.pt',
            215000000,
            'active'
        );
        """,
        """
        INSERT OR IGNORE INTO model_version (id, version, description, model_id, file_path, file_size, status)
        VALUES (
            '00000000-0000-0000-0000-000000000002',
            '2.0.0',
            'ResNet-50优化版本',
            '00000000-0000-0000-0000-000000000002',
            '/models/resnet50-v2.h5',
            98000000,
            'active'
        );
        """,
    ],
}


def log(message, level="INFO"):
    """简单的日志输出函数"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def init_db():
    """初始化数据库，创建表并插入示例数据"""
    log(f"正在初始化数据库 {DB_PATH}...")

    # 检查数据库文件所在目录是否存在
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # 连接数据库
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        log("数据库连接已建立")
    except sqlite3.Error as e:
        log(f"连接数据库失败: {e}", "ERROR")
        sys.exit(1)

    try:
        # 创建表
        log("正在创建数据库表...")
        for table_name, create_sql in CREATE_TABLES_SQL.items():
            try:
                cursor.execute(create_sql)
                log(f"表 {table_name} 已创建或已存在")
            except sqlite3.Error as e:
                log(f"创建表 {table_name} 失败: {e}", "ERROR")

        # 插入示例数据
        log("正在插入示例数据...")
        for table_name, sqls in SAMPLE_DATA_SQL.items():
            for sql in sqls:
                try:
                    cursor.execute(sql)
                    log(f"表 {table_name} 示例数据已插入或已存在")
                except sqlite3.Error as e:
                    log(f"插入 {table_name} 数据失败: {e}", "WARNING")

        # 提交更改
        conn.commit()
        log("所有更改已提交到数据库")
    except Exception as e:
        conn.rollback()
        log(f"操作数据库时出错: {e}", "ERROR")
        sys.exit(1)
    finally:
        # 关闭连接
        conn.close()
        log("数据库连接已关闭")

    log("数据库初始化完成！✓", "SUCCESS")

    # 显示数据库信息
    log("\n数据库信息:")
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in cursor.fetchall()]

        # 获取每个表的行数
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table};")
            count = cursor.fetchone()["count"]
            log(f"表 {table}: {count} 行")

        conn.close()
    except sqlite3.Error as e:
        log(f"获取数据库信息失败: {e}", "ERROR")


if __name__ == "__main__":
    init_db()
