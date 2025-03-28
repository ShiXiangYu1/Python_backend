#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型服务测试模块

测试模型服务的各项功能，包括创建、获取、更新、删除模型等操作。
确保AI模型的管理功能正常工作。
"""

import uuid
import pytest
import asyncio
from unittest.mock import MagicMock, patch
from typing import AsyncGenerator
from io import BytesIO

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.model import Model, ModelStatus, ModelFramework
from app.schemas.model import ModelCreate, ModelUpdate
from app.services.user import user_service
from app.services.model import model_service
from app.core.security import create_password_hash


@pytest.mark.asyncio
async def test_create_model(db_session: AsyncSession):
    """测试创建模型"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_model_user",
        email="model_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()
    
    # 创建模型
    model_in = ModelCreate(
        name="Test Model",
        description="This is a test model",
        framework=ModelFramework.TENSORFLOW,
        version="1.0.0",
        is_public=False
    )
    model = await model_service.create_with_owner(
        db=db_session, obj_in=model_in, owner_id=user.id
    )
    
    # 验证模型已创建
    assert model.name == "Test Model"
    assert model.description == "This is a test model"
    assert model.framework == ModelFramework.TENSORFLOW
    assert model.version == "1.0.0"
    assert model.is_public is False
    assert model.owner_id == user.id
    assert model.status == ModelStatus.UPLOADING  # 默认状态


@pytest.mark.asyncio
async def test_get_model(db_session: AsyncSession):
    """测试获取模型"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_get_model_user",
        email="get_model_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建模型
    model = Model(
        id=str(uuid.uuid4()),
        name="Get Model Test",
        description="This is a get model test",
        framework=ModelFramework.PYTORCH,
        version="1.0.0",
        is_public=True,
        status=ModelStatus.UPLOADED,
        owner_id=user.id
    )
    db_session.add(model)
    await db_session.flush()
    
    # 获取模型
    retrieved_model = await model_service.get(db=db_session, id=model.id)
    
    # 验证获取的模型
    assert retrieved_model is not None
    assert retrieved_model.id == model.id
    assert retrieved_model.name == "Get Model Test"
    assert retrieved_model.framework == ModelFramework.PYTORCH
    assert retrieved_model.is_public is True
    assert retrieved_model.owner_id == user.id


@pytest.mark.asyncio
async def test_get_nonexistent_model(db_session: AsyncSession):
    """测试获取不存在的模型"""
    # 生成一个不存在的ID
    nonexistent_id = str(uuid.uuid4())
    
    # 尝试获取不存在的模型
    model = await model_service.get(db=db_session, id=nonexistent_id)
    
    # 应该返回None
    assert model is None


@pytest.mark.asyncio
async def test_update_model(db_session: AsyncSession):
    """测试更新模型"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_update_model_user",
        email="update_model_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建模型
    model = Model(
        id=str(uuid.uuid4()),
        name="Update Model Test",
        description="This is an update model test",
        framework=ModelFramework.ONNX,
        version="1.0.0",
        is_public=False,
        status=ModelStatus.UPLOADED,
        owner_id=user.id
    )
    db_session.add(model)
    await db_session.flush()
    
    # 更新模型
    update_data = ModelUpdate(
        name="Updated Model Name",
        description="Updated description",
        is_public=True
    )
    updated_model = await model_service.update(
        db=db_session, db_obj=model, obj_in=update_data
    )
    
    # 验证更新结果
    assert updated_model.name == "Updated Model Name"
    assert updated_model.description == "Updated description"
    assert updated_model.is_public is True
    # 不应该更新的字段
    assert updated_model.framework == ModelFramework.ONNX  # 保持不变
    assert updated_model.version == "1.0.0"  # 保持不变


@pytest.mark.asyncio
async def test_delete_model(db_session: AsyncSession):
    """测试删除模型"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_delete_model_user",
        email="delete_model_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建模型
    model = Model(
        id=str(uuid.uuid4()),
        name="Delete Model Test",
        description="This is a delete model test",
        framework=ModelFramework.SKLEARN,
        version="1.0.0",
        is_public=False,
        status=ModelStatus.UPLOADED,
        owner_id=user.id
    )
    db_session.add(model)
    await db_session.flush()
    
    # 删除模型
    deleted_model = await model_service.remove(db=db_session, id=model.id)
    
    # 验证删除结果
    assert deleted_model is not None
    assert deleted_model.id == model.id
    
    # 确认模型已被删除
    model_after_delete = await model_service.get(db=db_session, id=model.id)
    assert model_after_delete is None


@pytest.mark.asyncio
async def test_get_multi_by_owner(db_session: AsyncSession):
    """测试获取用户拥有的所有模型"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_multi_models_user",
        email="multi_models_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()
    
    # 创建多个模型
    for i in range(3):
        model = Model(
            id=str(uuid.uuid4()),
            name=f"Multi Model Test {i}",
            description=f"This is multi model test {i}",
            framework=ModelFramework.TENSORFLOW,
            version="1.0.0",
            is_public=False,
            status=ModelStatus.UPLOADED,
            owner_id=user.id
        )
        db_session.add(model)
    await db_session.flush()
    
    # 获取用户的所有模型
    models = await model_service.get_multi_by_owner(
        db=db_session, owner_id=user.id, skip=0, limit=10
    )
    
    # 验证结果
    assert len(models) == 3
    for model in models:
        assert model.owner_id == user.id


@pytest.mark.asyncio
async def test_get_public_models(db_session: AsyncSession):
    """测试获取公开模型"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_public_models_user",
        email="public_models_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()
    
    # 创建公开和私有模型
    for i in range(2):
        model = Model(
            id=str(uuid.uuid4()),
            name=f"Public Model Test {i}",
            description=f"This is public model test {i}",
            framework=ModelFramework.TENSORFLOW,
            version="1.0.0",
            is_public=True,  # 公开模型
            status=ModelStatus.UPLOADED,
            owner_id=user.id
        )
        db_session.add(model)
    
    for i in range(2):
        model = Model(
            id=str(uuid.uuid4()),
            name=f"Private Model Test {i}",
            description=f"This is private model test {i}",
            framework=ModelFramework.TENSORFLOW,
            version="1.0.0",
            is_public=False,  # 私有模型
            status=ModelStatus.UPLOADED,
            owner_id=user.id
        )
        db_session.add(model)
    await db_session.flush()
    
    # 获取公开模型
    public_models = await model_service.get_public_models(
        db=db_session, skip=0, limit=10
    )
    
    # 验证结果
    assert len(public_models) == 2
    for model in public_models:
        assert model.is_public is True


@pytest.mark.asyncio
async def test_update_status(db_session: AsyncSession):
    """测试更新模型状态"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_status_model_user",
        email="status_model_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建模型
    model = Model(
        id=str(uuid.uuid4()),
        name="Status Model Test",
        description="This is a status model test",
        framework=ModelFramework.TENSORFLOW,
        version="1.0.0",
        is_public=False,
        status=ModelStatus.UPLOADING,  # 初始状态
        owner_id=user.id
    )
    db_session.add(model)
    await db_session.flush()
    
    # 更新模型状态
    updated_model = await model_service.update_status(
        db=db_session, model_id=model.id, status=ModelStatus.UPLOADED
    )
    
    # 验证更新结果
    assert updated_model is not None
    assert updated_model.status == ModelStatus.UPLOADED


@pytest.mark.asyncio
async def test_models_with_pagination(db_session: AsyncSession):
    """测试带分页的模型查询"""
    # 创建测试用户
    user = User(
        id=str(uuid.uuid4()),
        username="test_pagination_user",
        email="pagination_test@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()
    
    # 创建多个模型
    for i in range(10):
        model = Model(
            id=str(uuid.uuid4()),
            name=f"Pagination Model Test {i}",
            description=f"This is pagination model test {i}",
            framework=ModelFramework.TENSORFLOW,
            version="1.0.0",
            is_public=i % 2 == 0,  # 偶数索引为公开模型
            status=ModelStatus.UPLOADED,
            owner_id=user.id
        )
        db_session.add(model)
    await db_session.flush()
    
    # 测试分页 - 第一页
    models_page1, total = await model_service.get_models_with_pagination(
        db=db_session, owner_id=user.id, skip=0, limit=5
    )
    
    # 验证结果
    assert len(models_page1) == 5  # 第一页5条
    assert total == 10  # 总共10条
    
    # 测试分页 - 第二页
    models_page2, total = await model_service.get_models_with_pagination(
        db=db_session, owner_id=user.id, skip=5, limit=5
    )
    
    # 验证结果
    assert len(models_page2) == 5  # 第二页5条
    assert total == 10  # 总共10条
    
    # 测试不同页面的结果不同
    assert models_page1[0].id != models_page2[0].id
    
    # 测试只查询公开模型
    public_models, public_total = await model_service.get_models_with_pagination(
        db=db_session, public_only=True, skip=0, limit=10
    )
    
    # 验证结果
    assert len(public_models) == 5  # 5个公开模型
    assert public_total == 5  # 总共5个公开模型 