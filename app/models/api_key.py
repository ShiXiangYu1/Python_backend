#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API密钥模型模块

定义API密钥的数据库模型，用于管理和验证API调用的访问凭证。
支持API密钥的创建、验证和权限控制。
"""

import secrets
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base_class import BaseModel


class APIKey(BaseModel):
    """
    API密钥模型

    存储API密钥信息，用于验证API调用的合法性和权限控制。
    每个API密钥都关联到一个用户，并可以设置特定的权限范围和过期时间。
    """

    # 密钥信息
    name = Column(String(100), nullable=False, comment="密钥名称")
    key = Column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: secrets.token_hex(32),
        comment="密钥值",
    )

    # 权限信息
    scopes = Column(Text, nullable=True, comment="权限范围，多个范围用逗号分隔")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")

    # 过期信息
    expires_at = Column(DateTime, nullable=True, comment="过期时间，为空表示永不过期")

    # 使用统计
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")
    usage_count = Column(Integer, default=0, nullable=False, comment="使用次数")

    # 关系
    # 关联的用户（多对一）
    user_id = Column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    user = relationship("User", back_populates="api_keys")

    @property
    def is_expired(self) -> bool:
        """
        检查密钥是否已过期

        如果未设置过期时间则永不过期，否则比较当前时间和过期时间。

        返回:
            bool: 是否已过期
        """
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """
        检查密钥是否有效

        密钥必须激活且未过期才有效。

        返回:
            bool: 是否有效
        """
        return self.is_active and not self.is_expired

    def update_usage(self) -> None:
        """
        更新密钥使用情况

        更新最后使用时间和使用次数。

        返回:
            None
        """
        self.last_used_at = datetime.utcnow()
        self.usage_count += 1

    def __repr__(self) -> str:
        """模型的字符串表示"""
        return f"<APIKey(id={self.id}, name={self.name}, user_id={self.user_id}, is_valid={self.is_valid})>"
