#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户服务测试模块

测试用户服务层的功能，如用户创建、认证、更新等。
确保用户管理相关的业务逻辑正常工作。
"""

import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.services.user import user_service


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


# 创建用户测试
@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """测试创建用户"""
    # 准备测试数据
    user_in = UserCreate(**TEST_USER)
    
    # 调用被测试函数
    user = await user_service.create(db_session, obj_in=user_in)
    
    # 断言结果
    assert user.username == TEST_USER["username"]
    assert user.email == TEST_USER["email"]
    assert user.full_name == TEST_USER["full_name"]
    assert user.role == TEST_USER["role"]
    assert user.id is not None
    assert user.hashed_password is not None
    assert user.hashed_password != TEST_USER["password"]  # 密码已经被哈希


# 获取用户测试
@pytest.mark.asyncio
async def test_get_user(db_session: AsyncSession):
    """测试通过ID获取用户"""
    # 准备测试数据
    user_in = UserCreate(**TEST_USER)
    user = await user_service.create(db_session, obj_in=user_in)
    
    # 调用被测试函数
    retrieved_user = await user_service.get(db_session, user.id)
    
    # 断言结果
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.username == user.username
    assert retrieved_user.email == user.email


# 获取不存在的用户测试
@pytest.mark.asyncio
async def test_get_nonexistent_user(db_session: AsyncSession):
    """测试获取不存在的用户"""
    # 调用被测试函数
    non_existent_id = str(uuid.uuid4())
    retrieved_user = await user_service.get(db_session, non_existent_id)
    
    # 断言结果
    assert retrieved_user is None


# 通过用户名获取用户测试
@pytest.mark.asyncio
async def test_get_user_by_username(db_session: AsyncSession):
    """测试通过用户名获取用户"""
    # 准备测试数据
    user_in = UserCreate(**TEST_USER)
    user = await user_service.create(db_session, obj_in=user_in)
    
    # 调用被测试函数
    retrieved_user = await user_service.get_by_username(db_session, username=TEST_USER["username"])
    
    # 断言结果
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.username == user.username


# 通过邮箱获取用户测试
@pytest.mark.asyncio
async def test_get_user_by_email(db_session: AsyncSession):
    """测试通过邮箱获取用户"""
    # 准备测试数据
    user_in = UserCreate(**TEST_USER)
    user = await user_service.create(db_session, obj_in=user_in)
    
    # 调用被测试函数
    retrieved_user = await user_service.get_by_email(db_session, email=TEST_USER["email"])
    
    # 断言结果
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.email == user.email


# 更新用户测试
@pytest.mark.asyncio
async def test_update_user(db_session: AsyncSession):
    """测试更新用户信息"""
    # 准备测试数据
    user_in = UserCreate(**TEST_USER)
    user = await user_service.create(db_session, obj_in=user_in)
    
    # 更新数据
    new_full_name = "Updated Test User"
    update_data = UserUpdate(full_name=new_full_name)
    
    # 调用被测试函数
    updated_user = await user_service.update(db_session, db_obj=user, obj_in=update_data)
    
    # 断言结果
    assert updated_user.full_name == new_full_name
    assert updated_user.username == user.username  # 未更新的字段保持不变
    assert updated_user.email == user.email  # 未更新的字段保持不变


# 更新用户密码测试
@pytest.mark.asyncio
async def test_update_user_password(db_session: AsyncSession):
    """测试更新用户密码"""
    # 准备测试数据
    user_in = UserCreate(**TEST_USER)
    user = await user_service.create(db_session, obj_in=user_in)
    
    # 原始密码认证
    authenticated_user = await user_service.authenticate(
        db_session, 
        username_or_email=TEST_USER["username"], 
        password=TEST_USER["password"]
    )
    assert authenticated_user is not None
    
    # 更新密码
    new_password = "newpassword123"
    update_data = UserUpdate(password=new_password)
    
    # 调用被测试函数
    updated_user = await user_service.update(db_session, db_obj=user, obj_in=update_data)
    
    # 断言结果：原密码不再有效
    old_auth_user = await user_service.authenticate(
        db_session, 
        username_or_email=TEST_USER["username"], 
        password=TEST_USER["password"]
    )
    assert old_auth_user is None
    
    # 断言结果：新密码有效
    new_auth_user = await user_service.authenticate(
        db_session, 
        username_or_email=TEST_USER["username"], 
        password=new_password
    )
    assert new_auth_user is not None
    assert new_auth_user.id == user.id


# 认证用户测试
@pytest.mark.asyncio
async def test_authenticate_user(db_session: AsyncSession):
    """测试用户认证"""
    # 准备测试数据
    user_in = UserCreate(**TEST_USER)
    await user_service.create(db_session, obj_in=user_in)
    
    # 调用被测试函数 - 使用用户名
    authenticated_user = await user_service.authenticate(
        db_session, 
        username_or_email=TEST_USER["username"], 
        password=TEST_USER["password"]
    )
    
    # 断言结果
    assert authenticated_user is not None
    assert authenticated_user.username == TEST_USER["username"]
    
    # 调用被测试函数 - 使用邮箱
    authenticated_user = await user_service.authenticate(
        db_session, 
        username_or_email=TEST_USER["email"], 
        password=TEST_USER["password"]
    )
    
    # 断言结果
    assert authenticated_user is not None
    assert authenticated_user.email == TEST_USER["email"]
    
    # 调用被测试函数 - 错误密码
    authenticated_user = await user_service.authenticate(
        db_session, 
        username_or_email=TEST_USER["username"], 
        password="wrongpassword"
    )
    
    # 断言结果
    assert authenticated_user is None


# 获取用户列表测试
@pytest.mark.asyncio
async def test_get_users_with_pagination(db_session: AsyncSession):
    """测试获取分页用户列表"""
    # 准备测试数据 - 创建多个用户
    for i in range(5):
        user_data = TEST_USER.copy()
        user_data["username"] = f"testuser{i}"
        user_data["email"] = f"test{i}@example.com"
        user_in = UserCreate(**user_data)
        await user_service.create(db_session, obj_in=user_in)
    
    # 调用被测试函数 - 获取第一页（2条记录）
    users, total = await user_service.get_users_with_pagination(
        db_session, skip=0, limit=2
    )
    
    # 断言结果
    assert len(users) == 2
    assert total >= 5  # 至少有5条记录
    
    # 调用被测试函数 - 获取第二页（2条记录）
    users, total = await user_service.get_users_with_pagination(
        db_session, skip=2, limit=2
    )
    
    # 断言结果
    assert len(users) == 2
    assert total >= 5  # 至少有5条记录 