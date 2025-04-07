#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型服务模块

提供AI模型相关的业务逻辑实现，如模型上传、部署、监控等。
处理模型文件的存储、验证和版本控制。
"""

import os
import hashlib
import shutil
import uuid
import time
from typing import List, Optional, Union, Dict, Any, BinaryIO, Tuple

from fastapi import UploadFile
from sqlalchemy import select, func, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.metrics import record_model_operation, record_model_deployment_time
from app.models.model import Model, ModelVersion, ModelStatus
from app.schemas.model import (
    ModelCreate,
    ModelUpdate,
    ModelVersionCreate,
    ModelVersionUpdate,
)
from app.services.base import CRUDBase


class ModelService(CRUDBase[Model, ModelCreate, ModelUpdate]):
    """
    AI模型服务类

    继承自基础CRUD服务类，提供AI模型特定的业务逻辑。
    如模型文件处理、部署管理等。
    """

    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: ModelCreate, owner_id: str
    ) -> Model:
        """
        创建带所有者的模型

        创建一个与特定用户关联的AI模型。

        参数:
            db: 数据库会话
            obj_in: 模型创建数据
            owner_id: 所有者ID

        返回:
            Model: 创建的模型对象
        """
        db_obj = Model(
            name=obj_in.name,
            description=obj_in.description,
            framework=obj_in.framework,
            version=obj_in.version,
            is_public=obj_in.is_public,
            owner_id=owner_id,
            status=ModelStatus.UPLOADING,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        # 记录模型创建操作
        record_model_operation("create", str(db_obj.id), owner_id)

        return db_obj

    async def get_multi_by_owner(
        self, db: AsyncSession, *, owner_id: str, skip: int = 0, limit: int = 100
    ) -> List[Model]:
        """
        获取所有者的模型列表

        查询特定用户的AI模型列表，支持分页。

        参数:
            db: 数据库会话
            owner_id: 所有者ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        返回:
            List[Model]: 模型列表
        """
        query = (
            select(Model).where(Model.owner_id == owner_id).offset(skip).limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_public_models(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Model]:
        """
        获取公开模型列表

        查询所有公开的AI模型列表，支持分页。

        参数:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数

        返回:
            List[Model]: 公开模型列表
        """
        query = select(Model).where(Model.is_public == True).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def count_by_owner(self, db: AsyncSession, *, owner_id: str) -> int:
        """
        计算所有者的模型数量

        获取特定用户的AI模型总数。

        参数:
            db: 数据库会话
            owner_id: 所有者ID

        返回:
            int: 模型总数
        """
        query = (
            select(func.count()).select_from(Model).where(Model.owner_id == owner_id)
        )
        result = await db.execute(query)
        return result.scalar_one()

    async def get_models_with_pagination(
        self,
        db: AsyncSession,
        *,
        owner_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        public_only: bool = False,
    ) -> Tuple[List[Model], int]:
        """
        获取分页模型列表

        查询AI模型列表，支持按所有者过滤和分页，并返回总数。

        参数:
            db: 数据库会话
            owner_id: 所有者ID，可选
            skip: 跳过的记录数
            limit: 返回的最大记录数
            public_only: 是否只返回公开模型

        返回:
            Tuple[List[Model], int]: 模型列表和总数
        """
        # 构建查询条件
        conditions = []
        if owner_id:
            conditions.append(Model.owner_id == owner_id)
        if public_only:
            conditions.append(Model.is_public == True)
        
        # 创建基础查询，使用JOIN一次性加载关联数据
        # 减少 N+1 查询问题，适用于所有数据库
        query = select(Model).options(
            selectinload(Model.versions),  # 预加载版本信息
            selectinload(Model.owner)      # 预加载所有者信息
        )
        
        # 添加条件
        for condition in conditions:
            query = query.where(condition)
        
        # 添加排序 - 优先显示最新创建的模型
        query = query.order_by(desc(Model.created_at))
        
        # 获取数据库连接的方言名称，以适配不同数据库
        dialect_name = db.bind.dialect.name

        # 只有在使用PostgreSQL时才添加索引提示
        if dialect_name == 'postgresql':
            query = query.with_hint(
                Model, 
                "INDEX(models_owner_id_idx)", 
                dialect_name="postgresql"
            )
        
        # 添加分页
        query = query.offset(skip).limit(limit)

        # 执行查询并获取结果
        result = await db.execute(query)
        models = result.scalars().all()

        # 计算总数 - 使用优化的count查询
        # 通过先应用过滤条件再进行count，减少数据扫描量
        # 创建高效的计数查询 - 仅选择ID列以减少数据传输
        count_query = select(func.count(Model.id.distinct()))
        
        # 添加过滤条件
        for condition in conditions:
            count_query = count_query.where(condition)
            
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        return models, total

    async def update_status(
        self, db: AsyncSession, *, model_id: str, status: ModelStatus
    ) -> Optional[Model]:
        """
        更新模型状态

        更新AI模型的状态。

        参数:
            db: 数据库会话
            model_id: 模型ID
            status: 新状态

        返回:
            Optional[Model]: 更新后的模型，如果不存在则返回None
        """
        model = await self.get(db, model_id)
        if not model:
            return None

        model.status = status
        db.add(model)
        await db.commit()
        await db.refresh(model)

        # 记录模型状态更新操作
        record_model_operation("update_status", str(model.id), str(model.owner_id))

        return model

    async def upload_model_file(
        self, db: AsyncSession, *, model_id: str, file: UploadFile
    ) -> Optional[Model]:
        """
        上传模型文件

        将上传的文件保存到磁盘，并更新模型相关信息。

        参数:
            db: 数据库会话
            model_id: 模型ID
            file: 上传的文件

        返回:
            Optional[Model]: 更新后的模型，如果不存在则返回None
        """
        model = await self.get(db, model_id)
        if not model:
            return None

        # 确保上传目录存在
        os.makedirs(settings.MODEL_UPLOAD_DIR, exist_ok=True)

        # 生成文件路径
        file_path = os.path.join(
            settings.MODEL_UPLOAD_DIR, f"{model_id}_{os.path.basename(file.filename)}"
        )

        # 计算文件哈希并保存文件
        file_hash, file_size = await self._save_file_with_hash(file, file_path)

        # 更新模型信息
        model.file_path = file_path
        model.file_size = file_size
        model.file_hash = file_hash
        model.status = ModelStatus.UPLOADED

        db.add(model)
        await db.commit()
        await db.refresh(model)

        # 记录模型文件上传操作
        record_model_operation("upload", str(model.id), str(model.owner_id))

        return model

    async def _save_file_with_hash(
        self, file: UploadFile, file_path: str
    ) -> Tuple[str, int]:
        """
        保存文件并计算哈希值

        将文件保存到指定路径，同时计算MD5哈希值和文件大小。

        参数:
            file: 上传的文件
            file_path: 保存路径

        返回:
            Tuple[str, int]: 文件哈希值和大小
        """
        hash_md5 = hashlib.md5()
        file_size = 0

        # 创建目标文件
        with open(file_path, "wb") as buffer:
            # 分块读取文件
            while chunk := await file.read(8192):
                hash_md5.update(chunk)
                buffer.write(chunk)
                file_size += len(chunk)

        # 重置文件指针，以便后续操作
        await file.seek(0)

        return hash_md5.hexdigest(), file_size

    async def deploy_model(
        self, db: AsyncSession, *, model_id: str, config: Dict[str, Any] = None
    ) -> Optional[Model]:
        """
        部署模型

        将模型部署为API服务。

        参数:
            db: 数据库会话
            model_id: 模型ID
            config: 部署配置

        返回:
            Optional[Model]: 更新后的模型，如果不存在则返回None
        """
        model = await self.get(db, model_id)
        if not model:
            return None

        # 检查模型是否可以部署
        if model.status not in [
            ModelStatus.UPLOADED,
            ModelStatus.VALID,
            ModelStatus.UNDEPLOYED,
        ]:
            return None

        # 更新为部署中状态
        model.status = ModelStatus.DEPLOYING
        db.add(model)
        await db.commit()
        await db.refresh(model)

        # 记录部署开始时间
        start_time = time.time()

        # TODO: 实现实际的模型部署逻辑
        # 这里可以启动一个后台任务来处理部署

        # 模拟部署成功
        model.status = ModelStatus.DEPLOYED
        model.endpoint_url = f"/api/models/{model_id}/predict"

        db.add(model)
        await db.commit()
        await db.refresh(model)

        # 记录部署耗时
        duration = time.time() - start_time
        record_model_deployment_time(str(model.id), duration)

        # 记录模型部署操作
        record_model_operation("deploy", str(model.id), str(model.owner_id))

        return model


class ModelVersionService(
    CRUDBase[ModelVersion, ModelVersionCreate, ModelVersionUpdate]
):
    """
    模型版本服务类

    继承自基础CRUD服务类，提供模型版本特定的业务逻辑。
    处理版本控制和历史记录管理。
    """

    async def create_with_model(
        self, db: AsyncSession, *, obj_in: ModelVersionCreate, parent_model_id: str
    ) -> ModelVersion:
        """
        创建模型版本

        为特定模型创建一个新版本。

        参数:
            db: 数据库会话
            obj_in: 版本创建数据
            parent_model_id: 父模型ID

        返回:
            ModelVersion: 创建的版本对象
        """
        db_obj = ModelVersion(
            version=obj_in.version,
            change_log=obj_in.change_log,
            parent_model_id=parent_model_id,
            status=ModelStatus.UPLOADED,
            is_current=False,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_multi_by_model(
        self, db: AsyncSession, *, parent_model_id: str, skip: int = 0, limit: int = 100
    ) -> List[ModelVersion]:
        """
        获取模型的版本列表

        查询特定模型的版本列表，支持分页。

        参数:
            db: 数据库会话
            parent_model_id: 父模型ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        返回:
            List[ModelVersion]: 版本列表
        """
        query = (
            select(ModelVersion)
            .where(ModelVersion.parent_model_id == parent_model_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def set_current_version(
        self, db: AsyncSession, *, version_id: str, parent_model_id: str
    ) -> Optional[ModelVersion]:
        """
        设置当前版本

        将指定版本设置为模型的当前版本，同时取消其他版本的当前状态。

        参数:
            db: 数据库会话
            version_id: 版本ID
            parent_model_id: 父模型ID

        返回:
            Optional[ModelVersion]: 设置的当前版本，如果不存在则返回None
        """
        # 取消所有版本的当前状态
        query = select(ModelVersion).where(
            ModelVersion.parent_model_id == parent_model_id
        )
        result = await db.execute(query)
        versions = result.scalars().all()

        for version in versions:
            version.is_current = False
            db.add(version)

        # 设置指定版本为当前版本
        version = await self.get(db, version_id)
        if not version or version.parent_model_id != parent_model_id:
            return None

        version.is_current = True
        db.add(version)
        await db.commit()
        await db.refresh(version)

        return version

    async def upload_version_file(
        self, db: AsyncSession, *, version_id: str, file: UploadFile
    ) -> Optional[ModelVersion]:
        """
        上传版本文件

        将上传的文件保存到磁盘，并更新版本相关信息。

        参数:
            db: 数据库会话
            version_id: 版本ID
            file: 上传的文件

        返回:
            Optional[ModelVersion]: 更新后的版本，如果不存在则返回None
        """
        version = await self.get(db, version_id)
        if not version:
            return None

        # 确保上传目录存在
        os.makedirs(settings.MODEL_UPLOAD_DIR, exist_ok=True)

        # 生成文件路径
        file_path = os.path.join(
            settings.MODEL_UPLOAD_DIR,
            f"{version.parent_model_id}_{version.version}_{os.path.basename(file.filename)}",
        )

        # 计算文件哈希并保存文件
        file_hash, file_size = await self._save_file_with_hash(file, file_path)

        # 更新版本信息
        version.file_path = file_path
        version.file_size = file_size
        version.file_hash = file_hash

        db.add(version)
        await db.commit()
        await db.refresh(version)

        return version

    async def _save_file_with_hash(
        self, file: UploadFile, file_path: str
    ) -> Tuple[str, int]:
        """
        保存文件并计算哈希值

        将文件保存到指定路径，同时计算MD5哈希值和文件大小。

        参数:
            file: 上传的文件
            file_path: 保存路径

        返回:
            Tuple[str, int]: 文件哈希值和大小
        """
        hash_md5 = hashlib.md5()
        file_size = 0

        # 创建目标文件
        with open(file_path, "wb") as buffer:
            # 分块读取文件
            while chunk := await file.read(8192):
                hash_md5.update(chunk)
                buffer.write(chunk)
                file_size += len(chunk)

        # 重置文件指针，以便后续操作
        await file.seek(0)

        return hash_md5.hexdigest(), file_size


# 创建模型和版本服务单例
model_service = ModelService(Model)
model_version_service = ModelVersionService(ModelVersion)
