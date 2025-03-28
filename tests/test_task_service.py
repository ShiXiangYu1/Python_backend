#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务服务单元测试模块

测试任务服务层的功能，包括任务的创建、查询、更新和删除。
"""

import uuid
import pytest
from unittest.mock import patch, MagicMock

from app.models.task import Task, TaskStatus, TaskPriority
from app.services.task import TaskService


@pytest.fixture
def task_service():
    """
    任务服务测试fixture
    
    提供任务服务实例用于测试。
    
    返回:
        TaskService: 任务服务实例
    """
    return TaskService()


@pytest.fixture
def mock_celery_app():
    """
    模拟Celery应用fixture
    
    提供模拟的Celery应用，用于测试任务提交。
    
    返回:
        MagicMock: 模拟的Celery应用
    """
    with patch('app.core.celery.celery_app') as mock_app:
        # 设置mock的send_task方法返回值
        mock_task = MagicMock()
        mock_task.id = "mock-celery-task-id"
        mock_app.send_task.return_value = mock_task
        yield mock_app


@pytest.fixture
def mock_db_session():
    """
    模拟数据库会话fixture
    
    提供模拟的数据库会话，用于测试数据库操作。
    
    返回:
        MagicMock: 模拟的数据库会话
    """
    mock_session = MagicMock()
    
    # 模拟异步上下文管理器
    mock_session.__aenter__ = MagicMock(return_value=mock_session)
    mock_session.__aexit__ = MagicMock(return_value=None)
    
    # 模拟commit方法
    mock_session.commit = MagicMock(return_value=None)
    mock_session.refresh = MagicMock(return_value=None)
    
    # 模拟execute方法
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=mock_result)
    mock_result.first = MagicMock(return_value=None)
    mock_result.all = MagicMock(return_value=[])
    mock_result.scalar_one = MagicMock(return_value=0)
    
    mock_session.execute = MagicMock(return_value=mock_result)
    
    return mock_session


class TestTaskService:
    """
    任务服务测试类
    
    测试任务服务的各种功能。
    """
    
    @pytest.mark.asyncio
    async def test_create_task(self, task_service, mock_db_session, mock_celery_app):
        """
        测试创建任务
        
        验证任务创建功能是否正常工作。
        
        参数:
            task_service: 任务服务实例
            mock_db_session: 模拟的数据库会话
            mock_celery_app: 模拟的Celery应用
        """
        # 准备测试数据
        task_name = "测试任务"
        task_type = "test_task"
        celery_task_name = "app.tasks.common_tasks.long_running_task"
        user_id = uuid.uuid4()
        model_id = uuid.uuid4()
        priority = TaskPriority.HIGH
        
        # 模拟数据库添加任务后生成的任务对象
        mock_task = MagicMock(spec=Task)
        mock_task.id = uuid.uuid4()
        mock_task.name = task_name
        mock_task.task_type = task_type
        mock_task.status = TaskStatus.PENDING
        mock_task.priority = priority.value
        mock_task.user_id = user_id
        mock_task.model_id = model_id
        
        # 设置mock会话的add方法的行为
        def mock_add(task):
            nonlocal mock_task
            mock_task.args = task.args
            mock_task.kwargs = task.kwargs
            return None
            
        mock_db_session.add = MagicMock(side_effect=mock_add)
        
        # 执行测试
        task, celery_id = await task_service.create_task(
            db=mock_db_session,
            name=task_name,
            task_type=task_type,
            celery_task_name=celery_task_name,
            args=[10],
            kwargs={"param": "value"},
            user_id=user_id,
            model_id=model_id,
            priority=priority,
        )
        
        # 验证结果
        assert task == mock_task
        assert celery_id == "mock-celery-task-id"
        
        # 验证数据库操作
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called()
        mock_db_session.refresh.assert_called_with(mock_task)
        
        # 验证Celery任务提交
        mock_celery_app.send_task.assert_called_once_with(
            celery_task_name,
            args=[10],
            kwargs={"param": "value", "task_id": str(mock_task.id)},
            queue="high_priority",
        )
    
    @pytest.mark.asyncio
    async def test_get_task(self, task_service, mock_db_session):
        """
        测试获取任务
        
        验证根据ID获取任务的功能是否正常工作。
        
        参数:
            task_service: 任务服务实例
            mock_db_session: 模拟的数据库会话
        """
        # 准备测试数据
        task_id = uuid.uuid4()
        
        # 模拟数据库返回的任务
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.name = "测试任务"
        mock_task.status = TaskStatus.PENDING
        
        # 设置mock会话的execute方法返回值
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_result)
        mock_result.first = MagicMock(return_value=mock_task)
        mock_db_session.execute = MagicMock(return_value=mock_result)
        
        # 执行测试
        result = await task_service.get_task(mock_db_session, task_id)
        
        # 验证结果
        assert result == mock_task
        
        # 验证数据库操作
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_tasks(self, task_service, mock_db_session):
        """
        测试获取任务列表
        
        验证根据条件获取任务列表的功能是否正常工作。
        
        参数:
            task_service: 任务服务实例
            mock_db_session: 模拟的数据库会话
        """
        # 准备测试数据
        user_id = uuid.uuid4()
        mock_tasks = [
            MagicMock(spec=Task, id=uuid.uuid4(), name="任务1", status=TaskStatus.PENDING),
            MagicMock(spec=Task, id=uuid.uuid4(), name="任务2", status=TaskStatus.RUNNING),
        ]
        
        # 设置mock会话的execute方法返回值
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_result)
        mock_result.all = MagicMock(return_value=mock_tasks)
        mock_db_session.execute = MagicMock(return_value=mock_result)
        
        # 执行测试
        result = await task_service.get_tasks(
            db=mock_db_session,
            user_id=user_id,
            status=TaskStatus.PENDING,
            skip=0,
            limit=10,
        )
        
        # 验证结果
        assert result == mock_tasks
        
        # 验证数据库操作
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_task_status(self, task_service, mock_db_session):
        """
        测试更新任务状态
        
        验证更新任务状态的功能是否正常工作。
        
        参数:
            task_service: 任务服务实例
            mock_db_session: 模拟的数据库会话
        """
        # 准备测试数据
        task_id = uuid.uuid4()
        new_status = TaskStatus.RUNNING
        progress = 50
        result = {"progress": 50, "message": "任务进行中"}
        
        # 模拟获取任务的行为
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.status = TaskStatus.PENDING
        mock_task.progress = 0
        
        # 模拟task_service.get_task的行为
        with patch.object(task_service, 'get_task', return_value=mock_task) as mock_get_task:
            # 执行测试
            updated_task = await task_service.update_task_status(
                db=mock_db_session,
                task_id=task_id,
                status=new_status,
                progress=progress,
                result=result,
            )
            
            # 验证结果
            assert updated_task == mock_task
            assert mock_task.status == new_status
            assert mock_task.progress == progress
            assert mock_task.result == result
            
            # 验证方法调用
            mock_get_task.assert_called_once_with(mock_db_session, task_id)
            
            # 验证数据库操作
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once_with(mock_task)
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, task_service, mock_db_session):
        """
        测试取消任务
        
        验证取消任务的功能是否正常工作。
        
        参数:
            task_service: 任务服务实例
            mock_db_session: 模拟的数据库会话
        """
        # 准备测试数据
        task_id = uuid.uuid4()
        celery_id = "celery-task-id"
        
        # 模拟获取任务的行为
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.celery_id = celery_id
        mock_task.status = TaskStatus.RUNNING
        
        # 模拟task_service.get_task的行为
        with patch.object(task_service, 'get_task', return_value=mock_task) as mock_get_task:
            # 模拟CeleryHelper.cancel_task的行为
            with patch('app.core.celery.CeleryHelper.cancel_task', return_value=True) as mock_cancel:
                # 模拟task_service.update_task_status的行为
                with patch.object(task_service, 'update_task_status') as mock_update:
                    # 执行测试
                    result = await task_service.cancel_task(mock_db_session, task_id)
                    
                    # 验证结果
                    assert result is True
                    
                    # 验证方法调用
                    mock_get_task.assert_called_once_with(mock_db_session, task_id)
                    mock_cancel.assert_called_once_with(celery_id)
                    mock_update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_task(self, task_service, mock_db_session):
        """
        测试删除任务
        
        验证删除任务的功能是否正常工作。
        
        参数:
            task_service: 任务服务实例
            mock_db_session: 模拟的数据库会话
        """
        # 准备测试数据
        task_id = uuid.uuid4()
        
        # 模拟获取任务的行为
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.status = TaskStatus.SUCCEEDED
        
        # 模拟task_service.get_task的行为
        with patch.object(task_service, 'get_task', return_value=mock_task) as mock_get_task:
            # 执行测试
            result = await task_service.delete_task(mock_db_session, task_id)
            
            # 验证结果
            assert result is True
            
            # 验证方法调用
            mock_get_task.assert_called_once_with(mock_db_session, task_id)
            
            # 验证数据库操作
            mock_db_session.delete.assert_called_once_with(mock_task)
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_task_status_from_celery(self, task_service, mock_db_session):
        """
        测试从Celery同步任务状态
        
        验证从Celery同步任务状态的功能是否正常工作。
        
        参数:
            task_service: 任务服务实例
            mock_db_session: 模拟的数据库会话
        """
        # 准备测试数据
        task_id = uuid.uuid4()
        celery_id = "celery-task-id"
        
        # 模拟获取任务的行为
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.celery_id = celery_id
        mock_task.status = TaskStatus.RUNNING
        
        # 模拟Celery状态
        celery_status = {
            "id": celery_id,
            "status": "SUCCESS",
            "ready": True,
            "success": True,
            "result": {"message": "任务完成"},
            "progress": 100,
        }
        
        # 模拟task_service.get_task的行为
        with patch.object(task_service, 'get_task', return_value=mock_task) as mock_get_task:
            # 模拟CeleryHelper.get_task_status的行为
            with patch('app.core.celery.CeleryHelper.get_task_status', return_value=celery_status) as mock_get_status:
                # 模拟task_service.update_task_status的行为
                with patch.object(task_service, 'update_task_status') as mock_update:
                    # 执行测试
                    await task_service.sync_task_status_from_celery(mock_db_session, task_id)
                    
                    # 验证方法调用
                    mock_get_task.assert_called_once_with(mock_db_session, task_id)
                    mock_get_status.assert_called_once_with(celery_id)
                    mock_update.assert_called_once()
                    
                    # 验证更新参数是否正确
                    call_args = mock_update.call_args[1]
                    assert call_args["task_id"] == task_id
                    assert call_args["status"] == TaskStatus.SUCCEEDED
                    assert call_args["progress"] == 100
                    assert call_args["result"] == {"message": "任务完成"} 