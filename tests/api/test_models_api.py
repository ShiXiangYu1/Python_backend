#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型API测试模块

测试模型API的各项功能，包括创建、获取、更新、删除模型等操作。
确保模型管理相关的API端点正常工作并符合预期行为。
"""

import io
import uuid
import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.model import Model, ModelStatus, ModelFramework
from app.core.security import create_password_hash, create_access_token


@pytest.mark.asyncio
async def test_create_model(client: TestClient, db_session: AsyncSession):
    """测试创建模型"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="model_creator",
        email="model_creator@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    
    # 创建用户访问令牌
    access_token = create_access_token(subject=user_id)
    
    # 模型数据
    model_data = {
        "name": "Test Model",
        "description": "This is a test model",
        "framework": "tensorflow",
        "version": "1.0.0",
        "is_public": False
    }
    
    # 发送请求
    response = client.post(
        "/api/v1/models",
        headers={"Authorization": f"Bearer {access_token}"},
        json=model_data
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Model"
    assert data["description"] == "This is a test model"
    assert data["framework"] == "tensorflow"
    assert data["version"] == "1.0.0"
    assert data["is_public"] is False
    assert data["owner_id"] == user_id
    assert data["status"] == "uploading"  # 默认状态
    
    # 验证数据库中的模型
    model = await db_session.query(Model).filter(Model.name == "Test Model").first()
    assert model is not None
    assert model.owner_id == user_id
    assert model.framework == ModelFramework.TENSORFLOW


@pytest.mark.asyncio
async def test_get_models(client: TestClient, db_session: AsyncSession):
    """测试获取模型列表"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="model_list_user",
        email="model_list@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建多个模型
    for i in range(5):
        model = Model(
            id=str(uuid.uuid4()),
            name=f"List Test Model {i}",
            description=f"This is list test model {i}",
            framework=ModelFramework.TENSORFLOW,
            version="1.0.0",
            is_public=i % 2 == 0,  # 偶数索引为公开模型
            status=ModelStatus.UPLOADED,
            owner_id=user_id
        )
        db_session.add(model)
    
    await db_session.commit()
    
    # 创建用户访问令牌
    access_token = create_access_token(subject=user_id)
    
    # 发送请求 - 获取用户所有模型
    response = client.get(
        "/api/v1/models?page=1&page_size=10",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5  # 总共5个模型
    assert len(data["items"]) == 5  # 5个模型的列表
    
    # 发送请求 - 只获取公开模型
    response = client.get(
        "/api/v1/models?page=1&page_size=10&public_only=true",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3  # 3个公开模型


@pytest.mark.asyncio
async def test_get_public_models(client: TestClient, db_session: AsyncSession):
    """测试获取公开模型列表（不需要认证）"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="public_model_user",
        email="public_model@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建公开和私有模型
    for i in range(3):
        model = Model(
            id=str(uuid.uuid4()),
            name=f"Public Model {i}",
            description=f"This is public model {i}",
            framework=ModelFramework.TENSORFLOW,
            version="1.0.0",
            is_public=True,  # 公开模型
            status=ModelStatus.UPLOADED,
            owner_id=user_id
        )
        db_session.add(model)
    
    for i in range(2):
        model = Model(
            id=str(uuid.uuid4()),
            name=f"Private Model {i}",
            description=f"This is private model {i}",
            framework=ModelFramework.PYTORCH,
            version="1.0.0",
            is_public=False,  # 私有模型
            status=ModelStatus.UPLOADED,
            owner_id=user_id
        )
        db_session.add(model)
    
    await db_session.commit()
    
    # 发送请求 - 不需要认证
    response = client.get("/api/v1/models/public")
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3  # 3个公开模型
    for item in data["items"]:
        assert item["is_public"] is True


@pytest.mark.asyncio
async def test_get_model_by_id(client: TestClient, db_session: AsyncSession):
    """测试通过ID获取模型"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="model_get_user",
        email="model_get@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建模型
    model_id = str(uuid.uuid4())
    model = Model(
        id=model_id,
        name="Get Test Model",
        description="This is a get test model",
        framework=ModelFramework.PYTORCH,
        version="1.0.0",
        is_public=True,
        status=ModelStatus.UPLOADED,
        owner_id=user_id
    )
    db_session.add(model)
    await db_session.commit()
    
    # 创建用户访问令牌
    access_token = create_access_token(subject=user_id)
    
    # 发送请求
    response = client.get(
        f"/api/v1/models/{model_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == model_id
    assert data["name"] == "Get Test Model"
    assert data["framework"] == "pytorch"
    assert data["is_public"] is True
    assert data["owner_id"] == user_id


@pytest.mark.asyncio
async def test_update_model(client: TestClient, db_session: AsyncSession):
    """测试更新模型"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="model_update_user",
        email="model_update@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建模型
    model_id = str(uuid.uuid4())
    model = Model(
        id=model_id,
        name="Update Test Model",
        description="This is an update test model",
        framework=ModelFramework.ONNX,
        version="1.0.0",
        is_public=False,
        status=ModelStatus.UPLOADED,
        owner_id=user_id
    )
    db_session.add(model)
    await db_session.commit()
    
    # 创建用户访问令牌
    access_token = create_access_token(subject=user_id)
    
    # 更新数据
    update_data = {
        "name": "Updated Model Name",
        "description": "Updated description",
        "is_public": True
    }
    
    # 发送请求
    response = client.put(
        f"/api/v1/models/{model_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=update_data
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Model Name"
    assert data["description"] == "Updated description"
    assert data["is_public"] is True
    
    # 验证数据库中的更新
    await db_session.refresh(model)
    assert model.name == "Updated Model Name"
    assert model.description == "Updated description"
    assert model.is_public is True


@pytest.mark.asyncio
async def test_delete_model(client: TestClient, db_session: AsyncSession):
    """测试删除模型"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="model_delete_user",
        email="model_delete@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建模型
    model_id = str(uuid.uuid4())
    model = Model(
        id=model_id,
        name="Delete Test Model",
        description="This is a delete test model",
        framework=ModelFramework.SKLEARN,
        version="1.0.0",
        is_public=False,
        status=ModelStatus.UPLOADED,
        owner_id=user_id
    )
    db_session.add(model)
    await db_session.commit()
    
    # 创建用户访问令牌
    access_token = create_access_token(subject=user_id)
    
    # 发送请求
    response = client.delete(
        f"/api/v1/models/{model_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert "detail" in data  # 应返回成功消息
    
    # 验证模型已被删除
    deleted_model = await db_session.query(Model).filter(Model.id == model_id).first()
    assert deleted_model is None


@patch("app.services.model.ModelService._save_file_with_hash")
@pytest.mark.asyncio
async def test_upload_model_file(mock_save_file, client: TestClient, db_session: AsyncSession):
    """测试上传模型文件"""
    # 模拟文件保存
    mock_save_file.return_value = ("file_hash_value", 12345)
    
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="model_upload_user",
        email="model_upload@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建模型
    model_id = str(uuid.uuid4())
    model = Model(
        id=model_id,
        name="Upload Test Model",
        description="This is an upload test model",
        framework=ModelFramework.TENSORFLOW,
        version="1.0.0",
        is_public=False,
        status=ModelStatus.UPLOADING,  # 初始状态为上传中
        owner_id=user_id
    )
    db_session.add(model)
    await db_session.commit()
    
    # 创建用户访问令牌
    access_token = create_access_token(subject=user_id)
    
    # 模拟文件数据
    file_content = b"fake model file content"
    
    # 发送请求
    response = client.post(
        f"/api/v1/models/{model_id}/upload",
        headers={"Authorization": f"Bearer {access_token}"},
        files={"file": ("model.h5", io.BytesIO(file_content), "application/octet-stream")}
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == model_id
    assert data["status"] == "uploaded"  # 状态应该更新为已上传
    assert data["file_size"] == 12345
    
    # 验证数据库中的更新
    await db_session.refresh(model)
    assert model.status == ModelStatus.UPLOADED
    assert model.file_hash == "file_hash_value"
    assert model.file_size == 12345


@patch("app.services.model.ModelService.deploy_model")
@pytest.mark.asyncio
async def test_deploy_model_api(mock_deploy, client: TestClient, db_session: AsyncSession):
    """测试部署模型"""
    # 创建测试用户
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username="model_deploy_user",
        email="model_deploy@example.com",
        hashed_password=create_password_hash("password123"),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    
    # 创建模型
    model_id = str(uuid.uuid4())
    model = Model(
        id=model_id,
        name="Deploy Test Model",
        description="This is a deploy test model",
        framework=ModelFramework.TENSORFLOW,
        version="1.0.0",
        is_public=False,
        status=ModelStatus.UPLOADED,  # 已上传状态
        owner_id=user_id,
        file_path="/fake/path/model.h5",
        file_size=12345
    )
    db_session.add(model)
    await db_session.commit()
    
    # 模拟部署服务
    deployed_model = Model(
        id=model_id,
        name="Deploy Test Model",
        description="This is a deploy test model",
        framework=ModelFramework.TENSORFLOW,
        version="1.0.0",
        is_public=False,
        status=ModelStatus.DEPLOYED,  # 部署后的状态
        owner_id=user_id,
        file_path="/fake/path/model.h5",
        file_size=12345,
        endpoint_url="https://api.example.com/models/test-model"
    )
    mock_deploy.return_value = deployed_model
    
    # 创建用户访问令牌
    access_token = create_access_token(subject=user_id)
    
    # 部署配置
    deploy_config = {
        "config": {
            "instance_type": "cpu.small",
            "scaling": "auto"
        }
    }
    
    # 发送请求
    response = client.post(
        f"/api/v1/models/{model_id}/deploy",
        headers={"Authorization": f"Bearer {access_token}"},
        json=deploy_config
    )
    
    # 检查响应
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == model_id
    assert data["status"] == "deployed"
    assert data["endpoint_url"] == "https://api.example.com/models/test-model"
    
    # 验证模拟服务被调用
    mock_deploy.assert_called_once() 