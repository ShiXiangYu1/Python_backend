#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Redis缓存服务模块

提供Redis缓存服务，用于缓存任务状态、结果等数据，
减少数据库查询，提高系统性能。
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union, List
import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# 从环境变量或配置中获取Redis连接信息
REDIS_URL = os.getenv("REDIS_URL", settings.CELERY_BROKER_URL)
# 缓存过期时间（秒）
CACHE_EXPIRY = int(os.getenv("REDIS_CACHE_EXPIRY", "3600"))  # 默认1小时
# 任务状态缓存过期时间（秒）
TASK_STATUS_EXPIRY = int(os.getenv("TASK_STATUS_EXPIRY", "86400"))  # 默认1天
# 任务结果缓存过期时间（秒）
TASK_RESULT_EXPIRY = int(os.getenv("TASK_RESULT_EXPIRY", "604800"))  # 默认7天


class RedisCacheService:
    """
    Redis缓存服务类
    
    提供基于Redis的缓存功能，包括任务状态缓存、结果缓存等。
    使用Redis的哈希结构存储复杂对象，提高缓存效率。
    """
    
    _instance = None
    _redis_client = None
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(RedisCacheService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化Redis连接"""
        try:
            self._redis_client = redis.Redis.from_url(
                REDIS_URL, 
                socket_connect_timeout=5,
                socket_timeout=5,
                decode_responses=True  # 自动将字节解码为字符串
            )
            logger.info(f"Redis缓存服务已初始化，连接到: {REDIS_URL}")
            # 测试连接
            self._redis_client.ping()
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis连接失败: {e}")
            self._redis_client = None
        except Exception as e:
            logger.error(f"Redis初始化错误: {e}")
            self._redis_client = None
    
    def _ensure_connection(self):
        """确保Redis连接有效"""
        if self._redis_client is None:
            self._initialize()
        return self._redis_client is not None
    
    def set(self, key: str, value: Union[str, dict, list], expiry: int = CACHE_EXPIRY) -> bool:
        """
        设置缓存值
        
        参数:
            key: 缓存键
            value: 缓存值，可以是字符串、字典或列表
            expiry: 过期时间（秒）
            
        返回:
            bool: 操作是否成功
        """
        if not self._ensure_connection():
            return False
        
        try:
            # 转换为JSON字符串
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
                
            # 设置缓存
            self._redis_client.set(key, value, ex=expiry)
            return True
        except Exception as e:
            logger.error(f"设置缓存失败 [{key}]: {e}")
            return False
    
    def get(self, key: str, as_json: bool = False) -> Optional[Union[str, Dict, List]]:
        """
        获取缓存值
        
        参数:
            key: 缓存键
            as_json: 是否将结果解析为JSON对象
            
        返回:
            缓存值，可能是字符串、字典或列表，如果不存在则返回None
        """
        if not self._ensure_connection():
            return None
        
        try:
            # 获取缓存
            value = self._redis_client.get(key)
            
            # 如果值不存在，返回None
            if value is None:
                return None
                
            # 如果需要解析为JSON
            if as_json:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    logger.warning(f"无法将缓存值解析为JSON [{key}]")
                    return value
            
            return value
        except Exception as e:
            logger.error(f"获取缓存失败 [{key}]: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        参数:
            key: 缓存键
            
        返回:
            bool: 操作是否成功
        """
        if not self._ensure_connection():
            return False
        
        try:
            self._redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"删除缓存失败 [{key}]: {e}")
            return False
    
    def hmset(self, key: str, mapping: Dict[str, Any], expiry: int = CACHE_EXPIRY) -> bool:
        """
        设置哈希缓存
        
        参数:
            key: 哈希键
            mapping: 字段到值的映射
            expiry: 过期时间（秒）
            
        返回:
            bool: 操作是否成功
        """
        if not self._ensure_connection():
            return False
        
        try:
            # 将值转换为字符串
            string_mapping = {}
            for field, value in mapping.items():
                if isinstance(value, (dict, list)):
                    string_mapping[field] = json.dumps(value)
                else:
                    string_mapping[field] = str(value) if value is not None else ""
            
            # 设置哈希缓存
            self._redis_client.hset(key, mapping=string_mapping)
            
            # 设置过期时间
            if expiry > 0:
                self._redis_client.expire(key, expiry)
                
            return True
        except Exception as e:
            logger.error(f"设置哈希缓存失败 [{key}]: {e}")
            return False
    
    def hgetall(self, key: str, parse_json: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取哈希缓存的所有字段和值
        
        参数:
            key: 哈希键
            parse_json: 需要解析为JSON的字段列表
            
        返回:
            Dict[str, Any]: 字段到值的映射，如果不存在则返回None
        """
        if not self._ensure_connection():
            return None
        
        try:
            # 获取所有字段和值
            result = self._redis_client.hgetall(key)
            
            # 如果哈希不存在，返回None
            if not result:
                return None
            
            # 如果需要解析特定字段为JSON
            if parse_json:
                for field in parse_json:
                    if field in result and result[field]:
                        try:
                            result[field] = json.loads(result[field])
                        except json.JSONDecodeError:
                            logger.warning(f"无法将字段值解析为JSON [{key}][{field}]")
            
            return result
        except Exception as e:
            logger.error(f"获取哈希缓存失败 [{key}]: {e}")
            return None
    
    def hget(self, key: str, field: str, as_json: bool = False) -> Optional[Any]:
        """
        获取哈希缓存的特定字段值
        
        参数:
            key: 哈希键
            field: 字段名
            as_json: 是否将结果解析为JSON对象
            
        返回:
            字段值，如果不存在则返回None
        """
        if not self._ensure_connection():
            return None
        
        try:
            # 获取字段值
            value = self._redis_client.hget(key, field)
            
            # 如果字段不存在，返回None
            if value is None:
                return None
                
            # 如果需要解析为JSON
            if as_json:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    logger.warning(f"无法将字段值解析为JSON [{key}][{field}]")
                    return value
            
            return value
        except Exception as e:
            logger.error(f"获取哈希字段失败 [{key}][{field}]: {e}")
            return None
    
    def expire(self, key: str, expiry: int) -> bool:
        """
        设置缓存过期时间
        
        参数:
            key: 缓存键
            expiry: 过期时间（秒）
            
        返回:
            bool: 操作是否成功
        """
        if not self._ensure_connection():
            return False
        
        try:
            return self._redis_client.expire(key, expiry)
        except Exception as e:
            logger.error(f"设置缓存过期时间失败 [{key}]: {e}")
            return False
    
    def cache_task_status(self, task_id: str, status: Dict[str, Any]) -> bool:
        """
        缓存任务状态
        
        使用哈希结构缓存任务状态信息，提高查询性能。
        
        参数:
            task_id: 任务ID
            status: 任务状态信息
            
        返回:
            bool: 操作是否成功
        """
        key = f"task:{task_id}:status"
        return self.hmset(key, status, TASK_STATUS_EXPIRY)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态缓存
        
        参数:
            task_id: 任务ID
            
        返回:
            Dict[str, Any]: 任务状态信息，如果不存在则返回None
        """
        key = f"task:{task_id}:status"
        return self.hgetall(key, parse_json=["result"])
    
    def cache_task_result(self, task_id: str, result: Any) -> bool:
        """
        缓存任务结果
        
        参数:
            task_id: 任务ID
            result: 任务结果
            
        返回:
            bool: 操作是否成功
        """
        key = f"task:{task_id}:result"
        return self.set(key, result, TASK_RESULT_EXPIRY)
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """
        获取任务结果缓存
        
        参数:
            task_id: 任务ID
            
        返回:
            任务结果，如果不存在则返回None
        """
        key = f"task:{task_id}:result"
        return self.get(key, as_json=True)
    
    def invalidate_task_cache(self, task_id: str) -> bool:
        """
        使任务缓存失效
        
        删除与任务相关的所有缓存。
        
        参数:
            task_id: 任务ID
            
        返回:
            bool: 操作是否成功
        """
        status_key = f"task:{task_id}:status"
        result_key = f"task:{task_id}:result"
        try:
            self.delete(status_key)
            self.delete(result_key)
            return True
        except Exception as e:
            logger.error(f"使任务缓存失效失败 [{task_id}]: {e}")
            return False


# 导出单例实例
redis_cache = RedisCacheService() 