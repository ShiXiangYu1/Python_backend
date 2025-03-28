#!/bin/sh

set -e

# 等待数据库准备好
echo "等待数据库启动..."
sleep 5

# 运行数据库迁移
echo "运行数据库迁移..."
alembic upgrade head

# 初始化基础数据
echo "初始化基础数据..."
python scripts/seed_db_simple.py

# 启动应用
echo "启动应用..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@" 