#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型Schema模块

定义AI模型相关API的请求和响应数据模型，用于上传、部署和管理AI模型。
使用Pydantic模型进行数据验证和序列化。
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator

from app.models.model import ModelFramework, ModelStatus


# 基础模型信息
class ModelBase(BaseModel):
    """
    模型基础Schema

    包含AI模型的基本信息，作为创建和更新Schema的基类。
    """

    name: str = Field(..., min_length=1, max_length=100, description="模型名称")
    description: Optional[str] = Field(None, description="模型描述")
    framework: ModelFramework = Field(ModelFramework.CUSTOM, description="模型框架")
    version: str = Field("0.1.0", description="模型版本")
    is_public: bool = Field(False, description="是否公开")


# 创建模型
class ModelCreate(ModelBase):
    """
    创建模型Schema

    用于创建新AI模型的请求数据模型。
    实际文件上传通过表单处理，而不是JSON。
    """

    pass


# 更新模型
class ModelUpdate(BaseModel):
    """
    更新模型Schema

    用于更新AI模型信息的请求数据模型，所有字段都是可选的。
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模型名称")
    description: Optional[str] = Field(None, description="模型描述")
    framework: Optional[ModelFramework] = Field(None, description="模型框架")
    is_public: Optional[bool] = Field(None, description="是否公开")


# 模型部署
class ModelDeploy(BaseModel):
    """
    模型部署Schema

    用于部署AI模型的请求数据模型，包含部署配置信息。
    """

    config: Dict[str, Any] = Field({}, description="部署配置")


# 数据库中的模型
class ModelInDB(ModelBase):
    """
    数据库模型Schema

    表示数据库中存储的AI模型完整信息。
    """

    id: str = Field(..., description="模型ID")
    owner_id: str = Field(..., description="所有者ID")
    file_path: Optional[str] = Field(None, description="模型文件路径")
    file_size: Optional[int] = Field(None, description="模型文件大小(字节)")
    file_hash: Optional[str] = Field(None, description="模型文件哈希值")
    status: ModelStatus = Field(..., description="模型状态")
    endpoint_url: Optional[str] = Field(None, description="API端点URL")
    accuracy: Optional[float] = Field(None, description="准确率")
    latency: Optional[float] = Field(None, description="延迟(毫秒)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic配置类"""

        orm_mode = True


# API响应中的模型
class Model(ModelBase):
    """
    模型响应Schema

    用于API响应的AI模型信息模型。
    """

    id: str = Field(..., description="模型ID")
    owner_id: str = Field(..., description="所有者ID")
    file_name: Optional[str] = Field(None, description="模型文件名")
    file_size: Optional[int] = Field(None, description="模型文件大小(字节)")
    status: ModelStatus = Field(..., description="模型状态")
    endpoint_url: Optional[str] = Field(None, description="API端点URL")
    accuracy: Optional[float] = Field(None, description="准确率")
    latency: Optional[float] = Field(None, description="延迟(毫秒)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic配置类"""

        orm_mode = True


# 模型列表
class ModelList(BaseModel):
    """
    模型列表Schema

    用于返回AI模型列表的响应数据模型。
    """

    items: List[Model] = Field(..., description="模型列表")
    total: int = Field(..., description="总数")


# 模型版本基础信息
class ModelVersionBase(BaseModel):
    """
    模型版本基础Schema

    包含AI模型版本的基本信息。
    """

    version: str = Field(..., description="版本号")
    change_log: Optional[str] = Field(None, description="变更日志")


# 创建模型版本
class ModelVersionCreate(ModelVersionBase):
    """
    创建模型版本Schema

    用于创建新AI模型版本的请求数据模型。
    实际文件上传通过表单处理，而不是JSON。
    """

    pass


# 更新模型版本
class ModelVersionUpdate(BaseModel):
    """
    更新模型版本Schema

    用于更新AI模型版本信息的请求数据模型，所有字段都是可选的。
    """

    change_log: Optional[str] = Field(None, description="变更日志")
    is_current: Optional[bool] = Field(None, description="是否为当前版本")


# 数据库中的模型版本
class ModelVersionInDB(ModelVersionBase):
    """
    数据库模型版本Schema

    表示数据库中存储的AI模型版本完整信息。
    """

    id: str = Field(..., description="版本ID")
    parent_model_id: str = Field(..., description="所属模型ID")
    file_path: Optional[str] = Field(None, description="模型文件路径")
    file_size: Optional[int] = Field(None, description="模型文件大小(字节)")
    file_hash: Optional[str] = Field(None, description="模型文件哈希值")
    status: ModelStatus = Field(..., description="版本状态")
    is_current: bool = Field(..., description="是否为当前版本")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic配置类"""

        orm_mode = True


# API响应中的模型版本
class ModelVersion(ModelVersionBase):
    """
    模型版本响应Schema

    用于API响应的AI模型版本信息模型。
    """

    id: str = Field(..., description="版本ID")
    parent_model_id: str = Field(..., description="所属模型ID")
    file_size: Optional[int] = Field(None, description="模型文件大小(字节)")
    status: ModelStatus = Field(..., description="版本状态")
    is_current: bool = Field(..., description="是否为当前版本")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic配置类"""

        orm_mode = True


# 模型版本列表
class ModelVersionList(BaseModel):
    """
    模型版本列表Schema

    用于返回AI模型版本列表的响应数据模型。
    """

    items: List[ModelVersion] = Field(..., description="版本列表")
    total: int = Field(..., description="总数")
