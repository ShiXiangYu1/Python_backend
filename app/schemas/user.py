#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户Schema模块

定义用户相关API的请求和响应数据模型，用于数据验证和序列化。
基于Pydantic的BaseModel，提供数据类型检查、默认值和文档生成。
"""

from datetime import datetime
from typing import List, Optional
import html

from pydantic import BaseModel, EmailStr, Field, validator

from app.models.user import UserRole


# 共享属性
class UserBase(BaseModel):
    """
    用户基础Schema

    包含用户的基本信息，作为所有用户相关Schema的基类。
    """

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="电子邮箱")
    full_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="用户全名"
    )
    is_active: bool = Field(True, description="是否激活")
    role: UserRole = Field(UserRole.USER, description="用户角色")

    @validator("full_name")
    def sanitize_full_name(cls, v):
        """净化用户全名，防止XSS攻击"""
        if v is not None:
            # 使用html.escape转义HTML特殊字符防止XSS
            return html.escape(v)
        return v

    @validator("username")
    def sanitize_username(cls, v):
        """净化用户名，防止XSS攻击"""
        if v is not None:
            # 确保用户名不包含HTML特殊字符
            return html.escape(v)
        return v


# 创建用户
class UserCreate(UserBase):
    """
    创建用户Schema

    用于创建新用户的请求数据模型，包含密码字段。
    """

    password: str = Field(..., min_length=8, description="密码")
    confirm_password: str = Field(..., description="确认密码")

    @validator("confirm_password")
    def passwords_match(cls, v, values, **kwargs):
        """验证确认密码与密码相同"""
        if "password" in values and v != values["password"]:
            raise ValueError("密码和确认密码不匹配")
        return v


# 更新用户
class UserUpdate(BaseModel):
    """
    更新用户Schema

    用于更新用户信息的请求数据模型，所有字段都是可选的。
    """

    username: Optional[str] = Field(
        None, min_length=3, max_length=50, description="用户名"
    )
    email: Optional[EmailStr] = Field(None, description="电子邮箱")
    full_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="用户全名"
    )
    password: Optional[str] = Field(None, min_length=8, description="密码")
    is_active: Optional[bool] = Field(None, description="是否激活")
    role: Optional[UserRole] = Field(None, description="用户角色")


# 数据库中的用户
class UserInDB(UserBase):
    """
    数据库用户Schema

    表示数据库中存储的用户信息，包含哈希密码和ID。
    """

    id: str = Field(..., description="用户ID")
    hashed_password: str = Field(..., description="密码哈希")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic配置类"""

        orm_mode = True


# API响应中的用户
class User(UserBase):
    """
    用户响应Schema

    用于API响应的用户信息模型，不包含敏感信息。
    """

    id: str = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        """Pydantic配置类"""

        orm_mode = True


# 用户列表
class UserList(BaseModel):
    """
    用户列表Schema

    用于返回用户列表的响应数据模型。
    """

    items: List[User] = Field(..., description="用户列表")
    total: int = Field(..., description="总数")
