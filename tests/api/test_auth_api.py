#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
认证API测试模块

测试认证相关的API端点，如登录、注册等。
验证API端点的请求处理和响应生成是否符合预期。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import UserRole
from app.services.user import user_service
from app.schemas.user import UserCreate


# 测试数据
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword",
    "confirm_password": "testpassword",
    "full_name": "Test User",
    "is_active": True,
    "role": UserRole.USER
}


# 注册测试
def test_register(client: TestClient, db_session: AsyncSession):
    """测试用户注册"""
    # 准备请求数据
    response = client.post(
        f"{settings.API_PREFIX}/auth/register",
        json=TEST_USER
    )
    
    # 断言响应状态码和内容
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == TEST_USER["username"]
    assert data["email"] == TEST_USER["email"]
    assert data["full_name"] == TEST_USER["full_name"]
    assert "id" in data
    assert "hashed_password" not in data  # 不返回密码哈希
    assert "password" not in data  # 不返回密码


# 登录测试
@pytest.mark.asyncio
async def test_login(client: TestClient, db_session: AsyncSession):
    """测试用户登录"""
    # 创建测试用户
    user_in = UserCreate(**TEST_USER)
    await user_service.create(db_session, obj_in=user_in)
    
    # 准备表单数据
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        data={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    
    # 断言响应状态码和内容
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# JSON格式登录测试
@pytest.mark.asyncio
async def test_login_json(client: TestClient, db_session: AsyncSession):
    """测试JSON格式用户登录"""
    # 创建测试用户
    user_in = UserCreate(**TEST_USER)
    await user_service.create(db_session, obj_in=user_in)
    
    # 准备JSON数据
    response = client.post(
        f"{settings.API_PREFIX}/auth/login/json",
        json={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    
    # 断言响应状态码和内容
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# 使用邮箱登录测试
@pytest.mark.asyncio
async def test_login_with_email(client: TestClient, db_session: AsyncSession):
    """测试使用邮箱登录"""
    # 创建测试用户
    user_in = UserCreate(**TEST_USER)
    await user_service.create(db_session, obj_in=user_in)
    
    # 准备表单数据
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        data={
            "username": TEST_USER["email"],  # 使用邮箱
            "password": TEST_USER["password"]
        }
    )
    
    # 断言响应状态码和内容
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


# 密码错误登录测试
@pytest.mark.asyncio
async def test_login_wrong_password(client: TestClient, db_session: AsyncSession):
    """测试密码错误登录"""
    # 创建测试用户
    user_in = UserCreate(**TEST_USER)
    await user_service.create(db_session, obj_in=user_in)
    
    # 准备表单数据
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        data={
            "username": TEST_USER["username"],
            "password": "wrongpassword"
        }
    )
    
    # 断言响应状态码和内容
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "用户名或密码错误"


# 用户名不存在登录测试
def test_login_nonexistent_user(client: TestClient):
    """测试不存在用户登录"""
    # 准备表单数据
    response = client.post(
        f"{settings.API_PREFIX}/auth/login",
        data={
            "username": "nonexistentuser",
            "password": TEST_USER["password"]
        }
    )
    
    # 断言响应状态码和内容
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "用户名或密码错误"


# 重复用户名注册测试
@pytest.mark.asyncio
async def test_register_duplicate_username(client: TestClient, db_session: AsyncSession):
    """测试重复用户名注册"""
    # 创建测试用户
    user_in = UserCreate(**TEST_USER)
    await user_service.create(db_session, obj_in=user_in)
    
    # 准备重复用户名的数据
    duplicate_data = TEST_USER.copy()
    duplicate_data["email"] = "another@example.com"  # 不同的邮箱
    
    # 发送请求
    response = client.post(
        f"{settings.API_PREFIX}/auth/register",
        json=duplicate_data
    )
    
    # 断言响应状态码和内容
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "用户名已存在"


# 重复邮箱注册测试
@pytest.mark.asyncio
async def test_register_duplicate_email(client: TestClient, db_session: AsyncSession):
    """测试重复邮箱注册"""
    # 创建测试用户
    user_in = UserCreate(**TEST_USER)
    await user_service.create(db_session, obj_in=user_in)
    
    # 准备重复邮箱的数据
    duplicate_data = TEST_USER.copy()
    duplicate_data["username"] = "anotheruser"  # 不同的用户名
    
    # 发送请求
    response = client.post(
        f"{settings.API_PREFIX}/auth/register",
        json=duplicate_data
    )
    
    # 断言响应状态码和内容
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "邮箱已被注册"


# 密码不匹配注册测试
def test_register_passwords_dont_match(client: TestClient):
    """测试密码不匹配注册"""
    # 准备数据
    mismatched_data = TEST_USER.copy()
    mismatched_data["confirm_password"] = "differentpassword"
    
    # 发送请求
    response = client.post(
        f"{settings.API_PREFIX}/auth/register",
        json=mismatched_data
    )
    
    # 断言响应状态码和内容
    assert response.status_code == 422  # 验证错误
    data = response.json()
    assert "detail" in data 