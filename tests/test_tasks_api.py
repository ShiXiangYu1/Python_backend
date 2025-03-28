#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务API端点单元测试模块

测试任务API端点的功能，包括任务的创建、查询、更新、取消和删除。
"""

import uuid
import pytest
from unittest.mock import patch, MagicMock

from fastapi import status
from fastapi.testclient import TestClient

from app.models.task import Task, TaskStatus, TaskPriority
from app.models.user import User, UserRole
from app.main import app


@pytest.fixture
def test_client():
    """
    测试客户端fixture
    
    提供FastAPI测试客户端实例用于测试API。
    
    返回:
        TestClient: FastAPI测试客户端
    """
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """
    模拟当前用户fixture
    
    提供模拟的当前登录用户，用于测试需要认证的API。
    
    返回:
        User: 模拟用户对象
    """
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        role=UserRole.ADMIN,
    )
    return user


@pytest.fixture
def mock_task_service():
    """
    模拟任务服务fixture
    
    提供模拟的任务服务，用于测试API端点。
    
    返回:
        MagicMock: 模拟的任务服务
    """
    with patch('app.api.endpoints.tasks.task_service') as mock_service:
        yield mock_service


@pytest.fixture
def mock_get_current_active_user(mock_current_user):
    """
    模拟获取当前活跃用户fixture
    
    提供模拟的用户认证函数，用于测试需要认证的API。
    
    参数:
        mock_current_user: 模拟的当前用户
        
    返回:
        MagicMock: 模拟的获取当前用户函数
    """
    with patch('app.api.deps.get_current_active_user', return_value=mock_current_user) as mock_func:
        yield mock_func


class TestTasksAPI:
    """
    任务API端点测试类
    
    测试任务API的各种功能。
    """
    
    def test_create_task(self, test_client, mock_task_service, mock_get_current_active_user, mock_current_user):
        """
        测试创建任务API
        
        验证创建任务API端点是否正常工作。
        
        参数:
            test_client: FastAPI测试客户端
            mock_task_service: 模拟的任务服务
            mock_get_current_active_user: 模拟的获取当前用户函数
            mock_current_user: 模拟的当前用户
        """
        # 准备测试数据
        task_data = {
            "name": "测试任务",
            "task_type": "test_task",
            "celery_task_name": "app.tasks.common_tasks.long_running_task",
            "args": [10],
            "kwargs": {"param": "value"},
            "priority": TaskPriority.NORMAL,
        }
        
        # 模拟任务服务返回值
        mock_task = MagicMock(spec=Task)
        mock_task.id = uuid.uuid4()
        mock_task.name = task_data["name"]
        mock_task.task_type = task_data["task_type"]
        mock_task.status = TaskStatus.PENDING
        mock_task.priority = task_data["priority"]
        mock_task.user_id = mock_current_user.id
        mock_task.celery_id = "celery-task-id"
        
        # 设置mock的create_task方法返回值
        mock_task_service.create_task.return_value = (mock_task, "celery-task-id")
        
        # 发送请求
        response = test_client.post("/api/v1/tasks/", json=task_data)
        
        # 验证结果
        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.json()
        
        # 验证任务服务调用
        mock_task_service.create_task.assert_called_once()
        call_args = mock_task_service.create_task.call_args[1]
        assert call_args["name"] == task_data["name"]
        assert call_args["task_type"] == task_data["task_type"]
        assert call_args["celery_task_name"] == task_data["celery_task_name"]
        assert call_args["user_id"] == mock_current_user.id
    
    def test_list_tasks(self, test_client, mock_task_service, mock_get_current_active_user, mock_current_user):
        """
        测试获取任务列表API
        
        验证获取任务列表API端点是否正常工作。
        
        参数:
            test_client: FastAPI测试客户端
            mock_task_service: 模拟的任务服务
            mock_get_current_active_user: 模拟的获取当前用户函数
            mock_current_user: 模拟的当前用户
        """
        # 模拟任务列表
        mock_tasks = [
            MagicMock(spec=Task, id=uuid.uuid4(), name="任务1", status=TaskStatus.PENDING, user_id=mock_current_user.id),
            MagicMock(spec=Task, id=uuid.uuid4(), name="任务2", status=TaskStatus.RUNNING, user_id=mock_current_user.id),
        ]
        
        # 设置mock的get_tasks方法返回值
        mock_task_service.get_tasks.return_value = mock_tasks
        
        # 发送请求
        response = test_client.get("/api/v1/tasks/")
        
        # 验证结果
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
        assert len(response.json()) == len(mock_tasks)
        
        # 验证任务服务调用
        mock_task_service.get_tasks.assert_called_once()
    
    def test_get_task_count(self, test_client, mock_task_service, mock_get_current_active_user, mock_current_user):
        """
        测试获取任务统计API
        
        验证获取任务统计API端点是否正常工作。
        
        参数:
            test_client: FastAPI测试客户端
            mock_task_service: 模拟的任务服务
            mock_get_current_active_user: 模拟的获取当前用户函数
            mock_current_user: 模拟的当前用户
        """
        # 模拟任务统计数据
        mock_counts = {
            "total": 10,
            "pending": 3,
            "running": 2,
            "succeeded": 4,
            "failed": 1,
            "revoked": 0,
        }
        
        # 设置mock的get_task_count方法返回值
        mock_task_service.get_task_count.return_value = mock_counts
        
        # 发送请求
        response = test_client.get("/api/v1/tasks/count")
        
        # 验证结果
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_counts
        
        # 验证任务服务调用
        mock_task_service.get_task_count.assert_called_once()
    
    def test_get_task(self, test_client, mock_task_service, mock_get_current_active_user, mock_current_user):
        """
        测试获取任务详情API
        
        验证获取任务详情API端点是否正常工作。
        
        参数:
            test_client: FastAPI测试客户端
            mock_task_service: 模拟的任务服务
            mock_get_current_active_user: 模拟的获取当前用户函数
            mock_current_user: 模拟的当前用户
        """
        # 准备测试数据
        task_id = uuid.uuid4()
        
        # 模拟任务对象
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.name = "测试任务"
        mock_task.status = TaskStatus.RUNNING
        mock_task.user_id = mock_current_user.id
        
        # 设置mock的get_task方法返回值
        mock_task_service.get_task.return_value = mock_task
        
        # 发送请求
        response = test_client.get(f"/api/v1/tasks/{task_id}")
        
        # 验证结果
        assert response.status_code == status.HTTP_200_OK
        assert "id" in response.json()
        
        # 验证任务服务调用
        mock_task_service.get_task.assert_called_once_with(MagicMock(), task_id)
    
    def test_update_task(self, test_client, mock_task_service, mock_get_current_active_user, mock_current_user):
        """
        测试更新任务API
        
        验证更新任务API端点是否正常工作。
        
        参数:
            test_client: FastAPI测试客户端
            mock_task_service: 模拟的任务服务
            mock_get_current_active_user: 模拟的获取当前用户函数
            mock_current_user: 模拟的当前用户
        """
        # 准备测试数据
        task_id = uuid.uuid4()
        update_data = {
            "status": "running",
            "progress": 50,
            "result": {"message": "任务进行中"},
        }
        
        # 模拟任务对象
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.name = "测试任务"
        mock_task.status = TaskStatus.PENDING
        mock_task.user_id = mock_current_user.id
        
        # 模拟更新后的任务对象
        updated_mock_task = MagicMock(spec=Task)
        updated_mock_task.id = task_id
        updated_mock_task.name = "测试任务"
        updated_mock_task.status = TaskStatus.RUNNING
        updated_mock_task.progress = 50
        updated_mock_task.result = update_data["result"]
        updated_mock_task.user_id = mock_current_user.id
        
        # 设置mock的get_task和update_task_status方法返回值
        mock_task_service.get_task.return_value = mock_task
        mock_task_service.update_task_status.return_value = updated_mock_task
        
        # 发送请求
        response = test_client.patch(f"/api/v1/tasks/{task_id}", json=update_data)
        
        # 验证结果
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == update_data["status"]
        assert response.json()["progress"] == update_data["progress"]
        
        # 验证任务服务调用
        mock_task_service.get_task.assert_called_once()
        mock_task_service.update_task_status.assert_called_once()
    
    def test_cancel_task(self, test_client, mock_task_service, mock_get_current_active_user, mock_current_user):
        """
        测试取消任务API
        
        验证取消任务API端点是否正常工作。
        
        参数:
            test_client: FastAPI测试客户端
            mock_task_service: 模拟的任务服务
            mock_get_current_active_user: 模拟的获取当前用户函数
            mock_current_user: 模拟的当前用户
        """
        # 准备测试数据
        task_id = uuid.uuid4()
        
        # 模拟任务对象
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.status = TaskStatus.RUNNING
        mock_task.user_id = mock_current_user.id
        
        # 设置mock的get_task和cancel_task方法返回值
        mock_task_service.get_task.return_value = mock_task
        mock_task_service.cancel_task.return_value = True
        
        # 发送请求
        response = test_client.post(f"/api/v1/tasks/{task_id}/cancel")
        
        # 验证结果
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        
        # 验证任务服务调用
        mock_task_service.get_task.assert_called_once()
        mock_task_service.cancel_task.assert_called_once_with(MagicMock(), task_id)
    
    def test_delete_task(self, test_client, mock_task_service, mock_get_current_active_user, mock_current_user):
        """
        测试删除任务API
        
        验证删除任务API端点是否正常工作。
        
        参数:
            test_client: FastAPI测试客户端
            mock_task_service: 模拟的任务服务
            mock_get_current_active_user: 模拟的获取当前用户函数
            mock_current_user: 模拟的当前用户
        """
        # 准备测试数据
        task_id = uuid.uuid4()
        
        # 模拟任务对象
        mock_task = MagicMock(spec=Task)
        mock_task.id = task_id
        mock_task.status = TaskStatus.SUCCEEDED
        mock_task.user_id = mock_current_user.id
        
        # 设置mock的get_task和delete_task方法返回值
        mock_task_service.get_task.return_value = mock_task
        mock_task_service.delete_task.return_value = True
        
        # 发送请求
        response = test_client.delete(f"/api/v1/tasks/{task_id}")
        
        # 验证结果
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        
        # 验证任务服务调用
        mock_task_service.get_task.assert_called_once()
        mock_task_service.delete_task.assert_called_once_with(MagicMock(), task_id) 