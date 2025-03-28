#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API密钥API测试模块

测试API密钥相关的API端点，包括创建、获取、更新和删除API密钥等操作。
确保API密钥管理功能正常工作并符合预期行为。
"""

import uuid
import pytest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.api_key import APIKey
from app.core.security import create_password_hash, create_access_token


@pytest.mark.asyncio
async def test_create_api_key(client: TestClient, db_session: AsyncSession):
    """测试创建API密钥"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="api_key_creator",
        email="api_key_creator@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    
    # 创建用户访问令牌
    access_token = create_access_token(subject=user_id)
    
    # API密钥数据
    api_key_data = {
        "name": "Test API Key",
        "scopes": "read,write",
        "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
    }
    
    # 发送请求
    response = client.post(
        "/api/v1/api-keys",
        headers={"Authorization": f"Bearer {access_token}"},
        json=api_key_data
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test API Key"
    assert data["scopes"] == "read,write"
    assert data["user_id"] == user_id
    assert data["is_active"] is True
    assert data["key"] is not None  # 确保返回了密钥值
    assert len(data["key"]) == 64  # 32字节的十六进制表示
    
    # 验证数据库中的API密钥
    api_key = await db_session.query(APIKey).filter(APIKey.name == "Test API Key").first()
    assert api_key is not None
    assert api_key.user_id == user_id
    assert api_key.scopes == "read,write"


@pytest.mark.asyncio
async def test_get_api_keys(client: TestClient, db_session: AsyncSession):
    """测试获取API密钥列表"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="api_key_list_user",
        email="api_key_list@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建多个API密钥
    for i in range(5):
        api_key = APIKey(
            id=str(uuid.uuid4()),
            name=f"List Test Key {i}",
            key=f"listkey{i}" + "0" * 56,  # 64个字符
            user_id=user_id,
            scopes="read",
            is_active=True
        )
        db_session.add(api_key)
    
    await db_session.commit()
    
    # 创建用户访问令牌
    access_token = create_access_token(subject=user_id)
    
    # 发送请求 - 第一页
    response = client.get(
        "/api/v1/api-keys?page=1&page_size=3",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert len(data["items"]) == 3  # 第一页3个密钥
    assert data["total"] == 5  # 总共5个密钥
    
    # 发送请求 - 第二页
    response = client.get(
        "/api/v1/api-keys?page=2&page_size=3",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert len(data["items"]) == 2  # 第二页2个密钥


@pytest.mark.asyncio
async def test_get_api_key_by_id(client: TestClient, db_session: AsyncSession):
    """测试通过ID获取API密钥"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="api_key_get_user",
        email="api_key_get@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建API密钥
    api_key_id = str(uuid.uuid4())
    api_key = APIKey(
        id=api_key_id,
        name="Get Test Key",
        key="getkey" + "0" * 58,  # 64个字符
        user_id=user_id,
        scopes="read,write",
        is_active=True
    )
    db_session.add(api_key)
    await db_session.commit()
    
    # 创建用户访问令牌
    access_token = create_access_token(subject=user_id)
    
    # 发送请求
    response = client.get(
        f"/api/v1/api-keys/{api_key_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == api_key_id
    assert data["name"] == "Get Test Key"
    assert data["scopes"] == "read,write"
    assert data["user_id"] == user_id


@pytest.mark.asyncio
async def test_update_api_key(client: TestClient, db_session: AsyncSession):
    """测试更新API密钥"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="api_key_update_user",
        email="api_key_update@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建API密钥
    api_key_id = str(uuid.uuid4())
    api_key = APIKey(
        id=api_key_id,
        name="Update Test Key",
        key="updatekey" + "0" * 55,  # 64个字符
        user_id=user_id,
        scopes="read",
        is_active=True
    )
    db_session.add(api_key)
    await db_session.commit()
    
    # 创建用户访问令牌
    access_token = create_access_token(subject=user_id)
    
    # 更新数据
    update_data = {
        "name": "Updated Key Name",
        "scopes": "read,write,admin",
        "is_active": False
    }
    
    # 发送请求
    response = client.put(
        f"/api/v1/api-keys/{api_key_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=update_data
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Key Name"
    assert data["scopes"] == "read,write,admin"
    assert data["is_active"] is False
    
    # 验证数据库中的更新
    await db_session.refresh(api_key)
    assert api_key.name == "Updated Key Name"
    assert api_key.scopes == "read,write,admin"
    assert api_key.is_active is False


@pytest.mark.asyncio
async def test_delete_api_key(client: TestClient, db_session: AsyncSession):
    """测试删除API密钥"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="api_key_delete_user",
        email="api_key_delete@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建API密钥
    api_key_id = str(uuid.uuid4())
    api_key = APIKey(
        id=api_key_id,
        name="Delete Test Key",
        key="deletekey" + "0" * 55,  # 64个字符
        user_id=user_id,
        scopes="read",
        is_active=True
    )
    db_session.add(api_key)
    await db_session.commit()
    
    # 创建用户访问令牌
    access_token = create_access_token(subject=user_id)
    
    # 发送请求
    response = client.delete(
        f"/api/v1/api-keys/{api_key_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert "detail" in data  # 应返回成功消息
    
    # 验证API密钥已被删除
    deleted_key = await db_session.query(APIKey).filter(APIKey.id == api_key_id).first()
    assert deleted_key is None


@pytest.mark.asyncio
async def test_deactivate_api_key(client: TestClient, db_session: AsyncSession):
    """测试停用API密钥"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="api_key_deactivate_user",
        email="api_key_deactivate@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建API密钥
    api_key_id = str(uuid.uuid4())
    api_key = APIKey(
        id=api_key_id,
        name="Deactivate Test Key",
        key="deactivatekey" + "0" * 51,  # 64个字符
        user_id=user_id,
        scopes="read",
        is_active=True
    )
    db_session.add(api_key)
    await db_session.commit()
    
    # 创建用户访问令牌
    access_token = create_access_token(subject=user_id)
    
    # 发送请求
    response = client.post(
        f"/api/v1/api-keys/{api_key_id}/deactivate",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    
    # 验证数据库中的API密钥已停用
    await db_session.refresh(api_key)
    assert api_key.is_active is False


@pytest.mark.asyncio
async def test_get_other_user_api_key(client: TestClient, db_session: AsyncSession):
    """测试获取其他用户的API密钥（应该被拒绝）"""
    # 创建两个测试用户
    user1_id = str(uuid.uuid4())
    user1 = User(
        id=user1_id,
        username="api_key_user1",
        email="api_key_user1@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user1)
    
    user2_id = str(uuid.uuid4())
    user2 = User(
        id=user2_id,
        username="api_key_user2",
        email="api_key_user2@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user2)
    
    # 创建用户2的API密钥
    api_key_id = str(uuid.uuid4())
    api_key = APIKey(
        id=api_key_id,
        name="User2 Test Key",
        key="user2key" + "0" * 57,  # 64个字符
        user_id=user2_id,
        scopes="read",
        is_active=True
    )
    db_session.add(api_key)
    await db_session.commit()
    
    # 创建用户1的访问令牌
    access_token = create_access_token(subject=user1_id)
    
    # 发送请求，尝试获取用户2的API密钥
    response = client.get(
        f"/api/v1/api-keys/{api_key_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 检查响应 - 应该被拒绝
    assert response.status_code == 404  # 对于当前用户，该密钥不存在 