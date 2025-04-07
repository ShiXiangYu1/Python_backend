#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI模型模型模块

定义AI模型的数据库模型，存储模型的元数据、版本信息和部署状态等。
支持模型的上传、版本控制、部署和监控功能。
"""

import os
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Enum as SQLAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base_class import BaseModel


class ModelFramework(str, Enum):
    """
    模型框架枚举

    定义系统支持的AI模型框架类型。
    """

    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    ONNX = "onnx"
    SKLEARN = "sklearn"
    CUSTOM = "custom"


class ModelStatus(str, Enum):
    """
    模型状态枚举

    定义模型在平台中的状态流转。
    """

    UPLOADING = "uploading"  # 正在上传
    UPLOADED = "uploaded"  # 上传完成
    VALIDATING = "validating"  # 验证中
    VALID = "valid"  # 验证通过
    INVALID = "invalid"  # 验证失败
    DEPLOYING = "deploying"  # 部署中
    DEPLOYED = "deployed"  # 已部署
    UNDEPLOYED = "undeployed"  # 未部署
    ARCHIVED = "archived"  # 已归档


class Model(BaseModel):
    """
    AI模型模型

    存储AI模型的元数据、版本信息和部署状态等。
    支持模型的生命周期管理和版本控制。
    """

    # 模型基本信息
    name = Column(String(100), nullable=False, index=True, comment="模型名称")
    description = Column(Text, nullable=True, comment="模型描述")

    # 技术信息
    framework = Column(
        SQLAEnum(ModelFramework),
        nullable=False,
        default=ModelFramework.CUSTOM,
        comment="模型框架",
    )
    version = Column(String(20), nullable=False, default="0.1.0", comment="模型版本")

    # 模型文件信息
    file_path = Column(String(255), nullable=True, comment="模型文件路径")
    file_size = Column(Integer, nullable=True, comment="模型文件大小(字节)")
    file_hash = Column(String(64), nullable=True, comment="模型文件哈希值，用于完整性校验")

    # 模型状态和部署信息
    status = Column(
        SQLAEnum(ModelStatus),
        nullable=False,
        default=ModelStatus.UPLOADING,
        comment="模型状态",
    )
    is_public = Column(Boolean, default=False, nullable=False, comment="是否公开")
    endpoint_url = Column(String(255), nullable=True, comment="API端点URL")

    # 模型性能指标
    accuracy = Column(Float, nullable=True, comment="准确率")
    latency = Column(Float, nullable=True, comment="延迟(毫秒)")

    # 关系
    # 所属用户（多对一）
    owner_id = Column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    owner = relationship("User", back_populates="models")

    # 模型版本（一对多）
    versions = relationship(
        "ModelVersion", back_populates="parent_model", cascade="all, delete-orphan"
    )

    # 模型相关任务（一对多）
    tasks = relationship("Task", back_populates="model", cascade="all, delete-orphan")

    @property
    def file_name(self) -> Optional[str]:
        """
        获取模型文件名

        从文件路径中提取文件名。

        返回:
            Optional[str]: 文件名，如果路径不存在则返回None
        """
        if self.file_path:
            return os.path.basename(self.file_path)
        return None

    def update_status(self, status: ModelStatus) -> None:
        """
        更新模型状态

        更新模型的状态并处理相应的状态变更逻辑。

        参数:
            status: 新的模型状态

        返回:
            None
        """
        self.status = status

    def __repr__(self) -> str:
        """模型的字符串表示"""
        return f"<Model(id={self.id}, name={self.name}, framework={self.framework}, version={self.version}, status={self.status})>"


class ModelVersion(BaseModel):
    """
    模型版本模型

    存储模型的版本历史记录，支持模型的版本控制和回滚。
    每个版本关联到一个父模型。
    """

    # 版本信息
    version = Column(String(20), nullable=False, comment="版本号")
    change_log = Column(Text, nullable=True, comment="变更日志")

    # 文件信息
    file_path = Column(String(255), nullable=True, comment="模型文件路径")
    file_size = Column(Integer, nullable=True, comment="模型文件大小(字节)")
    file_hash = Column(String(64), nullable=True, comment="模型文件哈希值")

    # 状态信息
    status = Column(
        SQLAEnum(ModelStatus),
        nullable=False,
        default=ModelStatus.UPLOADED,
        comment="版本状态",
    )
    is_current = Column(Boolean, default=False, nullable=False, comment="是否为当前版本")

    # 关系
    # 所属模型（多对一）
    parent_model_id = Column(
        String(36), ForeignKey("model.id", ondelete="CASCADE"), nullable=False
    )
    parent_model = relationship("Model", back_populates="versions")

    def __repr__(self) -> str:
        """模型的字符串表示"""
        return f"<ModelVersion(id={self.id}, model_id={self.parent_model_id}, version={self.version}, is_current={self.is_current})>"
