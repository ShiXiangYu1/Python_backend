#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户API测试模块

测试用户API的各项功能，包括创建、获取、更新和删除用户等操作。
确保用户相关的API端点正常工作并符合预期行为。
"""

import json
import uuid
import pytest
from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.core.security import create_password_hash, create_access_token


def test_read_users_me(client: TestClient, db_session: AsyncSession):
    """测试获取当前用户信息"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    username = "test_me_user"
    email = "test_me@example.com"
    
    db_session.add(User(
        id=user_id,
        username=username,
        email=email,
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    ))
    db_session.commit()
    
    # 创建访问令牌
    access_token = create_access_token(
        subject=user_id
    )
    
    # 发送请求
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
    assert data["email"] == email
    assert data["id"] == user_id


def test_read_users_me_unauthorized(client: TestClient):
    """测试未授权访问当前用户信息"""
    # 发送请求，不提供令牌
    response = client.get("/api/v1/users/me")
    
    # 检查响应
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_me(client: TestClient, db_session: AsyncSession):
    """测试更新当前用户信息"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    username = "test_update_me_user"
    email = "test_update_me@example.com"
    
    user = User(
        id=user_id,
        username=username,
        email=email,
        full_name="Original Name",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    
    # 创建访问令牌
    access_token = create_access_token(
        subject=user_id
    )
    
    # 更新数据
    update_data = {
        "full_name": "Updated Full Name",
        "email": "updated_email@example.com"
    }
    
    # 发送请求
    response = client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json=update_data
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Full Name"
    assert data["email"] == "updated_email@example.com"
    
    # 验证数据库中的更新
    await db_session.refresh(user)
    assert user.full_name == "Updated Full Name"
    assert user.email == "updated_email@example.com"


@pytest.mark.asyncio
async def test_create_user_admin(client: TestClient, db_session: AsyncSession):
    """测试管理员创建用户"""
    # 创建管理员用户
    admin_id = str(uuid.uuid4())
    admin = User(
        id=admin_id,
        username="admin_user",
        email="admin@example.com",
        hashed_password=create_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    await db_session.commit()
    
    # 创建管理员访问令牌
    admin_token = create_access_token(
        subject=admin_id
    )
    
    # 新用户数据
    new_user_data = {
        "username": "new_test_user",
        "email": "new_test@example.com",
        "password": "newpassword123",
        "confirm_password": "newpassword123",
        "full_name": "New Test User",
        "role": "user"
    }
    
    # 发送请求
    response = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=new_user_data
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "new_test_user"
    assert data["email"] == "new_test@example.com"
    assert data["full_name"] == "New Test User"
    assert "hashed_password" not in data  # 不应泄露密码哈希
    
    # 验证数据库中的新用户
    user = await db_session.query(User).filter(User.username == "new_test_user").first()
    assert user is not None
    assert user.email == "new_test@example.com"
    assert user.role == UserRole.USER


@pytest.mark.asyncio
async def test_create_user_non_admin(client: TestClient, db_session: AsyncSession):
    """测试非管理员创建用户（应该被拒绝）"""
    # 创建普通用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="regular_user",
        email="regular@example.com",
        hashed_password=create_password_hash("regular123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    
    # 创建普通用户访问令牌
    user_token = create_access_token(
        subject=user_id
    )
    
    # 新用户数据
    new_user_data = {
        "username": "another_user",
        "email": "another@example.com",
        "password": "password123",
        "confirm_password": "password123",
        "full_name": "Another User",
        "role": "user"
    }
    
    # 发送请求
    response = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {user_token}"},
        json=new_user_data
    )
    
    # 检查响应 - 应该被拒绝
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_read_users_admin(client: TestClient, db_session: AsyncSession):
    """测试管理员获取用户列表"""
    # 创建管理员用户
    admin_id = str(uuid.uuid4())
    admin = User(
        id=admin_id,
        username="list_admin",
        email="list_admin@example.com",
        hashed_password=create_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    
    # 创建5个测试用户
    for i in range(5):
        user = User(
            id=str(uuid.uuid4()),
            username=f"list_user_{i}",
            email=f"list_user_{i}@example.com",
            hashed_password=create_password_hash("password123"),
            role=UserRole.USER,
            is_active=True
        )
        db_session.add(user)
    
    await db_session.commit()
    
    # 创建管理员访问令牌
    admin_token = create_access_token(
        subject=admin_id
    )
    
    # 发送请求 - 第一页
    response = client.get(
        "/api/v1/users?page=1&page_size=3",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert len(data["items"]) == 3  # 第一页3个用户
    
    # 发送请求 - 第二页
    response = client.get(
        "/api/v1/users?page=2&page_size=3",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert len(data["items"]) > 0  # 第二页至少有部分用户


@pytest.mark.asyncio
async def test_read_user_by_id_admin(client: TestClient, db_session: AsyncSession):
    """测试管理员通过ID获取用户"""
    # 创建管理员用户
    admin_id = str(uuid.uuid4())
    admin = User(
        id=admin_id,
        username="get_admin",
        email="get_admin@example.com",
        hashed_password=create_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="get_user",
        email="get_user@example.com",
        full_name="Get User",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    
    # 创建管理员访问令牌
    admin_token = create_access_token(
        subject=admin_id
    )
    
    # 发送请求
    response = client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["username"] == "get_user"
    assert data["email"] == "get_user@example.com"
    assert data["full_name"] == "Get User"


@pytest.mark.asyncio
async def test_update_user_admin(client: TestClient, db_session: AsyncSession):
    """测试管理员更新用户信息"""
    # 创建管理员用户
    admin_id = str(uuid.uuid4())
    admin = User(
        id=admin_id,
        username="update_admin",
        email="update_admin@example.com",
        hashed_password=create_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="update_user",
        email="update_user@example.com",
        full_name="Update User",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    
    # 创建管理员访问令牌
    admin_token = create_access_token(
        subject=admin_id
    )
    
    # 更新数据
    update_data = {
        "full_name": "Updated By Admin",
        "role": "admin",  # 提升为管理员
        "is_active": False  # 停用账户
    }
    
    # 发送请求
    response = client.put(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated By Admin"
    assert data["role"] == "admin"
    assert data["is_active"] is False
    
    # 验证数据库中的更新
    await db_session.refresh(user)
    assert user.full_name == "Updated By Admin"
    assert user.role == UserRole.ADMIN
    assert user.is_active is False


@pytest.mark.asyncio
async def test_delete_user_admin(client: TestClient, db_session: AsyncSession):
    """测试管理员删除用户"""
    # 创建管理员用户
    admin_id = str(uuid.uuid4())
    admin = User(
        id=admin_id,
        username="delete_admin",
        email="delete_admin@example.com",
        hashed_password=create_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="delete_user",
        email="delete_user@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    
    # 创建管理员访问令牌
    admin_token = create_access_token(
        subject=admin_id
    )
    
    # 发送请求
    response = client.delete(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert "detail" in data  # 应返回成功消息
    
    # 验证用户已被删除
    deleted_user = await db_session.query(User).filter(User.id == user_id).first()
    assert deleted_user is None 