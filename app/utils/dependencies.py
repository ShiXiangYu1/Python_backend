#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
依赖工具模块

提供API端点所需的各种依赖项，如数据库会话、当前用户、Redis客户端等。
这些依赖项可通过FastAPI的依赖注入系统使用。
"""

import redis
from fastapi import Depends

from app.core.config import settings


# Redis连接池
_redis_pool = None


def get_redis_client() -> redis.Redis:
    """
    获取Redis客户端实例

    使用连接池管理Redis连接，提高性能。

    返回:
        redis.Redis: Redis客户端实例
    """
    global _redis_pool

    # 如果连接池不存在，创建一个新的
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=False,
            max_connections=10,
            socket_timeout=5,
            socket_connect_timeout=5,
            health_check_interval=30,
        )

    # 从连接池获取连接
    return redis.Redis(connection_pool=_redis_pool)
