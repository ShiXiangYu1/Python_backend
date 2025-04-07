#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户模型模块

定义用户实体的数据库模型，包括用户的基本信息、认证信息和权限信息等。
作为认证和授权系统的基础模型。
"""

from enum import Enum
from typing import List, Optional

from sqlalchemy import Boolean, Column, String, Enum as SQLAEnum
from sqlalchemy.orm import relationship

from app.db.base_class import BaseModel


class UserRole(str, Enum):
    """
    用户角色枚举

    定义系统中的用户角色层级，用于权限控制。
    """

    SUPER_ADMIN = "super_admin"  # 超级管理员
    ADMIN = "admin"  # 管理员
    DEVELOPER = "developer"  # 开发者
    USER = "user"  # 普通用户


class User(BaseModel):
    """
    用户模型

    存储用户的基本信息、认证信息和权限信息。
    支持用户注册、登录、权限控制等功能。
    """

    # 用户基本信息
    username = Column(
        String(50), unique=True, index=True, nullable=False, comment="用户名"
    )
    email = Column(String(100), unique=True, index=True, nullable=False, comment="电子邮箱")
    full_name = Column(String(100), nullable=True, comment="用户全名")

    # 认证信息
    hashed_password = Column(String(100), nullable=False, comment="密码哈希")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")

    # 权限信息
    role = Column(
        SQLAEnum(UserRole), default=UserRole.USER, nullable=False, comment="用户角色"
    )

    # 关系
    # 用户拥有的模型（一对多）
    models = relationship("Model", back_populates="owner", cascade="all, delete-orphan")
    # 用户拥有的API密钥（一对多）
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    # 用户创建的任务（一对多）
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """模型的字符串表示"""
        return f"<User(id={self.id}, username={self.username}, email={self.email}, role={self.role})>"
