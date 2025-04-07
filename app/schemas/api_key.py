#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API密钥Schema模块

定义API密钥相关API的请求和响应数据模型，用于创建、查询和管理API密钥。
使用Pydantic模型进行数据验证和序列化。
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# 基础API密钥
class APIKeyBase(BaseModel):
    """
    API密钥基础Schema

    包含API密钥的基本信息，作为创建和更新Schema的基类。
    """

    name: str = Field(..., min_length=1, max_length=100, description="密钥名称")
    scopes: Optional[str] = Field(None, description="权限范围，多个范围用逗号分隔")
    is_active: bool = Field(True, description="是否激活")
    expires_at: Optional[datetime] = Field(None, description="过期时间，为空表示永不过期")


# 创建API密钥
class APIKeyCreate(APIKeyBase):
    """
    创建API密钥Schema

    用于创建新API密钥的请求数据模型。
    """

    pass


# 更新API密钥
class APIKeyUpdate(BaseModel):
    """
    更新API密钥Schema

    用于更新API密钥信息的请求数据模型，所有字段都是可选的。
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="密钥名称")
    scopes: Optional[str] = Field(None, description="权限范围，多个范围用逗号分隔")
    is_active: Optional[bool] = Field(None, description="是否激活")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


# 数据库中的API密钥
class APIKeyInDB(APIKeyBase):
    """
    数据库API密钥Schema

    表示数据库中存储的API密钥完整信息。
    """

    id: str = Field(..., description="密钥ID")
    key: str = Field(..., description="密钥值")
    user_id: str = Field(..., description="所属用户ID")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    usage_count: int = Field(0, description="使用次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic配置类"""

        orm_mode = True


# API响应中的API密钥
class APIKey(APIKeyBase):
    """
    API密钥响应Schema

    用于API响应的API密钥信息模型。
    """

    id: str = Field(..., description="密钥ID")
    key: str = Field(..., description="密钥值")
    user_id: str = Field(..., description="所属用户ID")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    usage_count: int = Field(0, description="使用次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    is_expired: bool = Field(False, description="是否已过期")
    is_valid: bool = Field(True, description="是否有效")

    class Config:
        """Pydantic配置类"""

        orm_mode = True


# 新创建的API密钥响应
class APIKeyCreated(APIKey):
    """
    新创建的API密钥响应Schema

    用于返回新创建的API密钥信息，特别强调密钥值，因为这是用户唯一可以看到密钥的机会。
    """

    pass


# API密钥列表
class APIKeyList(BaseModel):
    """
    API密钥列表Schema

    用于返回API密钥列表的响应数据模型。
    """

    items: List[APIKey] = Field(..., description="API密钥列表")
    total: int = Field(..., description="总数")
