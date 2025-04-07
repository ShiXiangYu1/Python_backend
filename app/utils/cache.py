#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
缓存工具模块

提供应用级别的缓存功能，优化API性能和减轻数据库负载。
实现了多级缓存策略，支持内存缓存和Redis缓存。
"""

import pickle
import hashlib
import json
import time
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TypeVar, cast

import redis
from fastapi import Request, Response
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.utils.dependencies import get_redis_client


# 类型变量
T = TypeVar("T")
CacheableResponse = TypeVar("CacheableResponse")


class CacheManager:
    """
    缓存管理器

    提供多级缓存功能，包括内存缓存和Redis缓存。
    支持缓存过期、自动刷新等功能。
    """

    # 内存缓存，仅用于本地开发环境或小型部署
    _memory_cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        初始化缓存管理器

        参数:
            redis_client: Redis客户端实例
        """
        self._redis = redis_client

    async def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值

        先从内存缓存获取，如果不存在则从Redis获取。

        参数:
            key: 缓存键
            default: 默认值

        返回:
            Any: 缓存值或默认值
        """
        # 先从内存缓存获取
        if key in self._memory_cache:
            cache_item = self._memory_cache[key]
            # 检查是否过期
            if cache_item.get("expires_at", float("inf")) > time.time():
                return cache_item.get("value", default)
            # 过期则移除
            self._memory_cache.pop(key, None)

        # 从Redis获取
        if self._redis:
            try:
                # 异步从Redis获取
                data = await run_in_threadpool(self._redis.get, key)
                if data:
                    # 反序列化数据
                    value = pickle.loads(data)
                    # 更新内存缓存
                    self._memory_cache[key] = {
                        "value": value,
                        "expires_at": time.time() + 60,  # 内存缓存60秒
                    }
                    return value
            except Exception as e:
                logging.error(f"Redis缓存获取错误: {str(e)}")

        return default

    async def set(
        self, key: str, value: Any, expire: int = 300, memory_only: bool = False
    ) -> bool:
        """
        设置缓存值

        同时更新内存缓存和Redis缓存。

        参数:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒）
            memory_only: 是否只缓存在内存中

        返回:
            bool: 操作是否成功
        """
        # 更新内存缓存
        self._memory_cache[key] = {
            "value": value,
            "expires_at": time.time() + min(expire, 300),  # 内存缓存最长5分钟
        }

        # 更新Redis缓存
        if self._redis and not memory_only:
            try:
                # 序列化数据
                data = pickle.dumps(value)
                # 异步设置Redis缓存
                result = await run_in_threadpool(self._redis.setex, key, expire, data)
                return result
            except Exception as e:
                logging.error(f"Redis缓存设置错误: {str(e)}")
                return False

        return True

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        同时从内存缓存和Redis缓存中删除。

        参数:
            key: 缓存键

        返回:
            bool: 操作是否成功
        """
        # 从内存缓存中删除
        self._memory_cache.pop(key, None)

        # 从Redis缓存中删除
        if self._redis:
            try:
                result = await run_in_threadpool(self._redis.delete, key)
                return bool(result)
            except Exception as e:
                logging.error(f"Redis缓存删除错误: {str(e)}")
                return False

        return True

    async def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的所有缓存

        参数:
            pattern: 键模式

        返回:
            int: 清除的键数量
        """
        # 清除内存缓存
        memory_cleared = 0
        for key in list(self._memory_cache.keys()):
            if key.startswith(pattern):
                self._memory_cache.pop(key, None)
                memory_cleared += 1

        # 清除Redis缓存
        redis_cleared = 0
        if self._redis:
            try:
                # 查找匹配的键
                keys = await run_in_threadpool(self._redis.keys, f"{pattern}*")
                if keys:
                    # 批量删除
                    redis_cleared = await run_in_threadpool(self._redis.delete, *keys)
            except Exception as e:
                logging.error(f"Redis缓存批量删除错误: {str(e)}")

        return memory_cleared + redis_cleared


# 全局缓存管理器实例
cache_manager = CacheManager()


def initialize_cache(redis_client: redis.Redis) -> None:
    """
    初始化缓存管理器

    参数:
        redis_client: Redis客户端实例
    """
    global cache_manager
    cache_manager = CacheManager(redis_client)


def cache(
    expire: int = 300, key_prefix: str = "cache:", vary_on_headers: List[str] = None
):
    """
    缓存装饰器

    用于缓存API路由的响应结果，减轻数据库负载。

    参数:
        expire: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
        vary_on_headers: 用于区分缓存的请求头列表

    返回:
        Callable: 装饰器函数
    """

    def decorator(
        func: Callable[..., CacheableResponse]
    ) -> Callable[..., CacheableResponse]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> CacheableResponse:
            # 查找Request参数
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request = value
                        break

            # 如果没有找到Request参数，或者是写操作，不使用缓存
            if not request or request.method not in ("GET", "HEAD", "OPTIONS"):
                return await func(*args, **kwargs)

            # 构建缓存键
            key_parts = [key_prefix, request.url.path]

            # 添加查询参数
            if request.query_params:
                key_parts.append(str(request.query_params))

            # 添加指定的请求头
            if vary_on_headers:
                for header in vary_on_headers:
                    if header.lower() in request.headers:
                        key_parts.append(f"{header}:{request.headers[header.lower()]}")

            # 生成缓存键
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            # 尝试从缓存获取
            cached_response = await cache_manager.get(cache_key)
            if cached_response is not None:
                # 返回缓存的响应
                response = cached_response
                # 添加缓存标识头
                if isinstance(response, Response):
                    response.headers["X-Cache"] = "HIT"
                return cast(CacheableResponse, response)

            # 执行原始处理函数
            response = await func(*args, **kwargs)

            # 如果是Response对象，添加缓存标识头
            if isinstance(response, Response):
                response.headers["X-Cache"] = "MISS"

            # 缓存响应
            await cache_manager.set(cache_key, response, expire)

            return response

        return wrapper

    return decorator


def invalidate_cache(prefix: str = "cache:") -> Callable:
    """
    缓存失效装饰器

    用于使指定前缀的缓存失效，通常用于写操作后。

    参数:
        prefix: 缓存键前缀

    返回:
        Callable: 装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 执行原始处理函数
            result = await func(*args, **kwargs)

            # 清除匹配的缓存
            await cache_manager.clear_pattern(prefix)

            return result

        return wrapper

    return decorator
