#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SQLAlchemyTask状态更新测试模块

测试SQLAlchemyTask中的_update_db_task_status方法，确保异步处理正常工作。
"""

import uuid
import time
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from app.tasks.common_tasks import SQLAlchemyTask
from app.models.task import TaskStatus
from app.services.task import TaskService


@pytest.fixture
def mock_redis_cache():
    """模拟Redis缓存"""
    with patch('app.tasks.common_tasks.redis_cache') as mock_cache:
        mock_cache.cache_task_status = MagicMock()
        yield mock_cache


@pytest.fixture
def mock_task_service():
    """模拟任务服务"""
    with patch('app.tasks.common_tasks.TaskService') as MockTaskService:
        mock_service = MockTaskService.return_value
        mock_service.update_task_status = AsyncMock()
        yield mock_service


@pytest.fixture
def mock_async_session():
    """模拟异步数据库会话"""
    async def _mock_async_session():
        mock_session = AsyncMock()
        yield mock_session
    
    with patch('app.tasks.common_tasks.async_session', _mock_async_session):
        yield


class TestSQLAlchemyTask:
    """SQLAlchemyTask测试类"""
    
    def test_init(self):
        """测试任务基类初始化"""
        task = SQLAlchemyTask()
        assert task._last_update_time == 0.0
        assert task._start_time == 0.0
        assert task._metrics == {
            'total_time': 0.0,
            'db_time': 0.0,
            'processing_time': 0.0,
            'db_operations': 0,
        }
    
    def test_update_db_task_status(self, mock_redis_cache, mock_task_service, mock_async_session):
        """测试任务状态更新方法"""
        task = SQLAlchemyTask()
        task_id = str(uuid.uuid4())
        status = TaskStatus.RUNNING
        progress = 50
        result = {"data": "test"}
        error = None
        
        # 调用更新方法
        task._update_db_task_status(
            task_id=task_id,
            status=status,
            progress=progress,
            result=result,
            error=error
        )
        
        # 验证缓存更新调用
        mock_redis_cache.cache_task_status.assert_called_once()
        args, kwargs = mock_redis_cache.cache_task_status.call_args
        assert args[0] == task_id
        assert args[1]["status"] == status.value
        assert args[1]["progress"] == progress
        assert args[1]["result"] == result
        
        # 由于异步更新是在一个新的事件循环中执行的，我们需要给它一点时间完成
        time.sleep(0.1)
        
        # 验证任务服务的update_task_status是否被正确调用
        mock_task_service.update_task_status.assert_awaited_once()
        args, kwargs = mock_task_service.update_task_status.await_args
        assert kwargs["task_id"] == uuid.UUID(task_id)
        assert kwargs["status"] == status
        assert kwargs["progress"] == progress
        assert kwargs["result"] == result
        assert kwargs["error"] == error
    
    def test_update_db_task_status_with_enum_status(self, mock_redis_cache, mock_task_service, mock_async_session):
        """测试使用枚举状态更新任务状态"""
        task = SQLAlchemyTask()
        task_id = str(uuid.uuid4())
        status = TaskStatus.SUCCEEDED
        
        # 调用更新方法
        task._update_db_task_status(
            task_id=task_id,
            status=status
        )
        
        # 验证缓存更新调用
        args, kwargs = mock_redis_cache.cache_task_status.call_args
        assert args[1]["status"] == status.value
    
    def test_update_db_task_status_with_string_status(self, mock_redis_cache, mock_task_service, mock_async_session):
        """测试使用字符串状态更新任务状态"""
        task = SQLAlchemyTask()
        task_id = str(uuid.uuid4())
        status = "completed"  # 字符串状态
        
        # 调用更新方法
        task._update_db_task_status(
            task_id=task_id,
            status=status
        )
        
        # 验证缓存更新调用
        args, kwargs = mock_redis_cache.cache_task_status.call_args
        assert args[1]["status"] == status
    
    def test_update_db_task_status_with_error(self, mock_redis_cache, mock_task_service, mock_async_session):
        """测试带错误信息的任务状态更新"""
        task = SQLAlchemyTask()
        task_id = str(uuid.uuid4())
        status = TaskStatus.FAILED
        error = {"error": "测试错误", "traceback": "测试堆栈跟踪"}
        
        # 调用更新方法
        task._update_db_task_status(
            task_id=task_id,
            status=status,
            error=error
        )
        
        # 验证缓存更新调用
        args, kwargs = mock_redis_cache.cache_task_status.call_args
        assert args[1]["status"] == status.value
        assert args[1]["error"] == error
    
    @patch('app.tasks.common_tasks.logger')
    def test_update_db_task_status_exception(self, mock_logger, mock_redis_cache):
        """测试状态更新异常处理"""
        task = SQLAlchemyTask()
        task_id = str(uuid.uuid4())
        status = TaskStatus.RUNNING
        
        # 模拟缓存更新异常
        mock_redis_cache.cache_task_status.side_effect = Exception("测试异常")
        
        # 调用更新方法（不应该抛出异常）
        task._update_db_task_status(
            task_id=task_id,
            status=status
        )
        
        # 验证异常被记录
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        assert "更新任务状态失败" in args[0] 