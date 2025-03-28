#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
健康检查API测试模块

测试健康检查端点，确保系统状态监控功能正常工作。
包括正常情况下的健康检查和数据库连接异常情况下的测试。
"""

import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


def test_health_check(client: TestClient, db_session: AsyncSession):
    """测试健康检查端点 - 正常情况"""
    # 发送请求
    response = client.get("/api/v1/health")
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    
    # 验证响应数据
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert data["database"] == "connected"
    assert "environment" in data


@patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
def test_health_check_db_error(mock_execute, client: TestClient, db_session: AsyncSession):
    """测试健康检查端点 - 数据库连接异常"""
    # 模拟数据库执行异常
    mock_execute.side_effect = Exception("Database connection error")
    
    # 发送请求
    response = client.get("/api/v1/health")
    
    # 检查响应
    assert response.status_code == 200  # 即使数据库错误，端点应该仍然返回200
    data = response.json()
    
    # 验证响应数据
    assert data["status"] == "unhealthy"
    assert "timestamp" in data
    assert "version" in data
    assert data["database"] == "disconnected"
    assert "database_error" in data