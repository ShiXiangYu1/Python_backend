#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库模型基类

提供数据库模型的通用基类，包含共享属性和方法，如创建时间、
更新时间和ID字段等。所有业务模型都应继承此基类。
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func

from app.db.session import Base


class BaseModel(Base):
    """
    数据库模型的基类

    为所有模型提供通用字段和功能，如ID、创建时间、更新时间、
    表名自动生成等。确保所有模型具有一致的基础结构。
    """

    # 将类标记为抽象，不创建对应的表
    __abstract__ = True

    # 自动生成表名为小写类名(蛇形命名)
    @declared_attr
    def __tablename__(cls) -> str:
        """自动生成表名为小写类名"""
        # 将CamelCase转换为snake_case
        name = cls.__name__
        return "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip(
            "_"
        )

    # 主键ID，使用UUID
    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )

    # 时间戳字段
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        将模型转换为字典

        用于API响应，将模型的所有字段转换为字典格式。

        返回:
            Dict[str, Any]: 模型的字典表示
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        从字典更新模型

        根据传入的字典更新模型的属性值。只更新模型已有的属性。

        参数:
            data: 包含要更新的属性键值对的字典

        返回:
            None
        """
        for field, value in data.items():
            if hasattr(self, field):
                setattr(self, field, value)
