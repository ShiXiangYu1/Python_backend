#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务服务单元测试示例模块

该模块展示了如何对任务服务层进行单元测试。
包含了创建任务、查询任务、更新任务状态等功能的测试。
"""

import unittest
import uuid
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

import pytest

from app.models.task import Task, TaskStatus, TaskPriority
from app.services.task import TaskService


class TestTaskService(unittest.TestCase):
    """
    任务服务测试类
    
    测试任务服务的各种功能。
    """
    
    def setUp(self):
        """
        测试初始化
        
        在每个测试方法执行前设置测试环境。
        """
        # 创建任务服务实例
        self.task_service = TaskService()
        
        # 创建模拟的数据库会话
        self.mock_db = MagicMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.refresh = AsyncMock()
        
        # 模拟任务数据
        self.task_id = uuid.uuid4()
        self.user_id = uuid.uuid4()
        self.model_id = uuid.uuid4()
        self.task_name = "测试任务"
        self.task_type = "test_task"
        self.celery_task_name = "app.tasks.common_tasks.long_running_task"

    @pytest.mark.asyncio
    async def test_create_task(self):
        """
        测试创建任务
        
        验证任务创建功能是否正常工作，包括：
        1. 数据库操作是否正确
        2. Celery任务是否提交
        3. 任务状态是否正确设置
        """
        # 准备测试数据
        task = Task(
            id=self.task_id,
            name=self.task_name,
            task_type=self.task_type,
            status=TaskStatus.PENDING,
            priority=TaskPriority.NORMAL.value,
            user_id=self.user_id,
            model_id=self.model_id,
            created_at=datetime.utcnow()
        )
        
        # 设置模拟的数据库add方法
        self.mock_db.add = MagicMock()
        
        # 设置模拟的Celery任务
        mock_celery_task = MagicMock()
        mock_celery_task.id = "mock-celery-task-id"
        
        # 模拟Celery的send_task方法
        with patch('app.core.celery.celery_app.send_task', return_value=mock_celery_task):
            # 执行测试
            result_task, celery_id = await self.task_service.create_task(
                db=self.mock_db,
                name=self.task_name,
                task_type=self.task_type,
                celery_task_name=self.celery_task_name,
                args=[10],
                kwargs={"param": "value"},
                user_id=self.user_id,
                model_id=self.model_id,
                priority=TaskPriority.NORMAL
            )
            
            # 验证数据库操作
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called()
            self.mock_db.refresh.assert_called()
            
            # 验证任务属性
            self.assertEqual(result_task.name, self.task_name)
            self.assertEqual(result_task.task_type, self.task_type)
            self.assertEqual(result_task.status, TaskStatus.PENDING)
            
            # 验证Celery任务ID
            self.assertEqual(celery_id, "mock-celery-task-id")

    @pytest.mark.asyncio
    async def test_get_task(self):
        """
        测试获取任务
        
        验证根据ID获取任务的功能是否正常工作。
        """
        # 准备模拟的任务
        mock_task = MagicMock(spec=Task)
        mock_task.id = self.task_id
        mock_task.name = self.task_name
        mock_task.status = TaskStatus.PENDING
        
        # 设置模拟的数据库查询结果
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_result)
        mock_result.first = MagicMock(return_value=mock_task)
        
        # 模拟数据库执行查询
        self.mock_db.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        result = await self.task_service.get_task(self.mock_db, self.task_id)
        
        # 验证结果
        self.assertEqual(result, mock_task)
        self.mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_status(self):
        """
        测试更新任务状态
        
        验证更新任务状态的功能是否正常工作，包括：
        1. 数据库查询是否正确
        2. 任务状态是否正确更新
        3. 任务进度是否正确更新
        """
        # 准备模拟的任务
        mock_task = MagicMock(spec=Task)
        mock_task.id = self.task_id
        mock_task.name = self.task_name
        mock_task.status = TaskStatus.PENDING
        
        # 设置模拟的数据库查询结果
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_result)
        mock_result.first = MagicMock(return_value=mock_task)
        
        # 模拟数据库执行查询
        self.mock_db.execute = AsyncMock(return_value=mock_result)
        
        # 执行测试
        new_status = TaskStatus.RUNNING
        progress = 50
        result_data = {"step": "processing", "details": "任务处理中"}
        
        updated_task = await self.task_service.update_task_status(
            db=self.mock_db,
            task_id=self.task_id,
            status=new_status,
            progress=progress,
            result=result_data
        )
        
        # 验证任务状态更新
        self.assertEqual(updated_task.status, new_status)
        self.assertEqual(updated_task.progress, progress)
        self.assertEqual(updated_task.result, result_data)
        
        # 验证数据库操作
        self.mock_db.execute.assert_called_once()
        self.mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_task(self):
        """
        测试取消任务
        
        验证取消任务的功能是否正常工作，包括：
        1. 数据库查询是否正确
        2. Celery任务是否被撤销
        3. 任务状态是否更新为已取消
        """
        # 准备模拟的任务
        mock_task = MagicMock(spec=Task)
        mock_task.id = self.task_id
        mock_task.name = self.task_name
        mock_task.status = TaskStatus.RUNNING
        mock_task.celery_id = "celery-task-id"
        
        # 设置模拟的数据库查询结果
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_result)
        mock_result.first = MagicMock(return_value=mock_task)
        
        # 模拟数据库执行查询
        self.mock_db.execute = AsyncMock(return_value=mock_result)
        
        # 模拟Celery的revoke方法
        with patch('app.core.celery.celery_app.control.revoke') as mock_revoke:
            # 执行测试
            success = await self.task_service.cancel_task(self.mock_db, self.task_id)
            
            # 验证结果
            self.assertTrue(success)
            
            # 验证Celery任务撤销
            mock_revoke.assert_called_once_with(
                "celery-task-id", 
                terminate=True, 
                signal="SIGTERM"
            )
            
            # 验证任务状态更新
            self.assertEqual(mock_task.status, TaskStatus.REVOKED)
            
            # 验证数据库操作
            self.mock_db.execute.assert_called_once()
            self.mock_db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main() 