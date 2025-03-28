#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API密钥服务测试模块

测试API密钥服务的各项功能，包括创建、获取、验证和删除API密钥等操作。
确保API密钥的生命周期管理功能正常工作。
"""

import uuid
import pytest
from datetime import datetime, timedelta
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate, APIKeyUpdate
from app.services.user import user_service
from app.services.api_key import api_key_service
from app.core.security import create_password_hash


@pytest.mark.asyncio
async def test_create_api_key(db_session: AsyncSession):
    """测试创建API密钥"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_api_key_user",
        email="api_key_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()
    
    # 创建API密钥
    api_key_in = APIKeyCreate(
        name="Test API Key",
        scopes="read,write",
    )
    api_key = await api_key_service.create_with_user(
        db=db_session, obj_in=api_key_in, user_id=user.id
    )
    
    # 验证API密钥已创建
    assert api_key.name == "Test API Key"
    assert api_key.scopes == "read,write"
    assert api_key.user_id == user.id
    assert api_key.is_active is True
    assert api_key.key is not None
    assert len(api_key.key) == 64  # 32字节的十六进制表示


@pytest.mark.asyncio
async def test_get_api_key(db_session: AsyncSession):
    """测试获取API密钥"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_get_key_user",
        email="get_key_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建API密钥
    api_key = APIKey(
        id=str(uuid.uuid4()),
        name="Get Key Test",
        key="testkey" + "0" * 58,  # 64个字符
        user_id=user.id,
        scopes="read",
        is_active=True
    )
    db_session.add(api_key)
    await db_session.flush()
    
    # 获取API密钥
    retrieved_key = await api_key_service.get(db=db_session, id=api_key.id)
    
    # 验证获取的API密钥
    assert retrieved_key is not None
    assert retrieved_key.id == api_key.id
    assert retrieved_key.name == "Get Key Test"
    assert retrieved_key.key == "testkey" + "0" * 58
    assert retrieved_key.user_id == user.id


@pytest.mark.asyncio
async def test_get_api_key_by_key(db_session: AsyncSession):
    """测试通过密钥值获取API密钥"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_get_by_key_user",
        email="get_by_key_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建API密钥
    test_key = "getbykey" + "0" * 57  # 64个字符
    api_key = APIKey(
        id=str(uuid.uuid4()),
        name="Get By Key Test",
        key=test_key,
        user_id=user.id,
        scopes="read",
        is_active=True
    )
    db_session.add(api_key)
    await db_session.flush()
    
    # 通过密钥值获取API密钥
    retrieved_key = await api_key_service.get_by_key(db=db_session, key=test_key)
    
    # 验证获取的API密钥
    assert retrieved_key is not None
    assert retrieved_key.id == api_key.id
    assert retrieved_key.key == test_key


@pytest.mark.asyncio
async def test_verify_valid_api_key(db_session: AsyncSession):
    """测试验证有效的API密钥"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_verify_key_user",
        email="verify_key_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建有效的API密钥
    test_key = "validkey" + "0" * 58  # 64个字符
    api_key = APIKey(
        id=str(uuid.uuid4()),
        name="Valid Key Test",
        key=test_key,
        user_id=user.id,
        scopes="read",
        is_active=True,
        # 将来过期时间
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db_session.add(api_key)
    await db_session.flush()
    
    # 验证API密钥
    verified_key = await api_key_service.verify_key(db=db_session, key=test_key)
    
    # 检查验证结果
    assert verified_key is not None
    assert verified_key.id == api_key.id
    assert verified_key.usage_count == 1  # 使用计数应该增加
    assert verified_key.last_used_at is not None  # 最后使用时间应该更新


@pytest.mark.asyncio
async def test_verify_expired_api_key(db_session: AsyncSession):
    """测试验证过期的API密钥"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_expired_key_user",
        email="expired_key_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建已过期的API密钥
    test_key = "expiredkey" + "0" * 56  # 64个字符
    api_key = APIKey(
        id=str(uuid.uuid4()),
        name="Expired Key Test",
        key=test_key,
        user_id=user.id,
        scopes="read",
        is_active=True,
        # 过期时间设置为过去
        expires_at=datetime.utcnow() - timedelta(days=1)
    )
    db_session.add(api_key)
    await db_session.flush()
    
    # 验证API密钥
    verified_key = await api_key_service.verify_key(db=db_session, key=test_key)
    
    # 过期的密钥应该验证失败
    assert verified_key is None


@pytest.mark.asyncio
async def test_verify_inactive_api_key(db_session: AsyncSession):
    """测试验证未激活的API密钥"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_inactive_key_user",
        email="inactive_key_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建未激活的API密钥
    test_key = "inactivekey" + "0" * 55  # 64个字符
    api_key = APIKey(
        id=str(uuid.uuid4()),
        name="Inactive Key Test",
        key=test_key,
        user_id=user.id,
        scopes="read",
        is_active=False,  # 未激活
    )
    db_session.add(api_key)
    await db_session.flush()
    
    # 验证API密钥
    verified_key = await api_key_service.verify_key(db=db_session, key=test_key)
    
    # 未激活的密钥应该验证失败
    assert verified_key is None


@pytest.mark.asyncio
async def test_update_api_key(db_session: AsyncSession):
    """测试更新API密钥"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_update_key_user",
        email="update_key_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建API密钥
    api_key = APIKey(
        id=str(uuid.uuid4()),
        name="Update Key Test",
        key="updatekey" + "0" * 56,  # 64个字符
        user_id=user.id,
        scopes="read",
        is_active=True
    )
    db_session.add(api_key)
    await db_session.flush()
    
    # 更新API密钥
    update_data = APIKeyUpdate(
        name="Updated Key Name",
        scopes="read,write",
        is_active=False
    )
    updated_key = await api_key_service.update(
        db=db_session, db_obj=api_key, obj_in=update_data
    )
    
    # 验证更新结果
    assert updated_key.name == "Updated Key Name"
    assert updated_key.scopes == "read,write"
    assert updated_key.is_active is False


@pytest.mark.asyncio
async def test_deactivate_api_key(db_session: AsyncSession):
    """测试停用API密钥"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_deactivate_key_user",
        email="deactivate_key_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建API密钥
    api_key = APIKey(
        id=str(uuid.uuid4()),
        name="Deactivate Key Test",
        key="deactivatekey" + "0" * 52,  # 64个字符
        user_id=user.id,
        scopes="read",
        is_active=True
    )
    db_session.add(api_key)
    await db_session.flush()
    
    # 停用API密钥
    deactivated_key = await api_key_service.deactivate(db=db_session, id=api_key.id)
    
    # 验证停用结果
    assert deactivated_key is not None
    assert deactivated_key.is_active is False


@pytest.mark.asyncio
async def test_get_multi_by_user(db_session: AsyncSession):
    """测试获取用户的所有API密钥"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_multi_keys_user",
        email="multi_keys_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()
    
    # 创建多个API密钥
    for i in range(3):
        api_key = APIKey(
            id=str(uuid.uuid4()),
            name=f"Multi Key Test {i}",
            key=f"multikey{i}" + "0" * 56,  # 64个字符
            user_id=user.id,
            scopes="read",
            is_active=True
        )
        db_session.add(api_key)
    await db_session.flush()
    
    # 获取用户的所有API密钥
    keys = await api_key_service.get_multi_by_user(
        db=db_session, user_id=user.id, skip=0, limit=10
    )
    
    # 验证结果
    assert len(keys) == 3
    for key in keys:
        assert key.user_id == user.id 