#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务模型模块

该模块定义了系统中任务的数据库模型，包括任务的基本信息、
状态追踪、关联用户和模型等。任务是系统中的异步操作单位，
用于处理如模型部署、训练、数据处理等耗时操作。
"""

import uuid
import enum
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, JSON, Enum
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class TaskStatus(str, enum.Enum):
    """
    任务状态枚举类

    定义了任务在其生命周期中可能的状态值。

    属性:
        PENDING: 任务已创建但尚未开始执行
        RUNNING: 任务正在执行中
        SUCCEEDED: 任务已成功完成
        FAILED: 任务执行失败
        REVOKED: 任务被取消或撤销
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REVOKED = "revoked"


class TaskPriority(int, enum.Enum):
    """
    任务优先级枚举类

    定义了任务的优先级别，用于决定任务执行的顺序。

    属性:
        LOW: 低优先级，值为1
        NORMAL: 普通优先级，值为2
        HIGH: 高优先级，值为3
        CRITICAL: 关键优先级，值为4
    """

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class Task(Base):
    """
    任务数据库模型

    表示系统中的异步任务，记录任务的详细信息、状态和执行结果。
    任务可以关联到特定用户和模型，用于跟踪谁创建了任务以及任务操作的是哪个模型。

    属性:
        id: 任务唯一标识符，UUID格式
        name: 任务名称
        task_type: 任务类型，如"模型部署"、"模型训练"等
        status: 任务当前状态，使用TaskStatus枚举
        priority: 任务优先级，使用TaskPriority枚举
        celery_id: Celery任务ID，用于关联到Celery任务
        args: 任务参数，JSON格式存储
        kwargs: 任务关键字参数，JSON格式存储
        result: 任务执行结果，JSON格式存储
        error: 任务执行错误信息
        progress: 任务执行进度，0-100的整数
        created_at: 任务创建时间
        started_at: 任务开始执行时间
        completed_at: 任务完成时间
        user_id: 关联的用户ID，表示谁创建了这个任务
        model_id: 关联的模型ID，表示任务操作的是哪个模型
    """

    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    task_type = Column(String(50), nullable=False, index=True)
    status = Column(
        Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True
    )
    priority = Column(Integer, default=TaskPriority.NORMAL, nullable=False)
    celery_id = Column(String(255), nullable=True, unique=True, index=True)
    args = Column(JSON, nullable=True)
    kwargs = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    progress = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    user_id = Column(String(36), ForeignKey("user.id"), nullable=True, index=True)
    user = relationship("User", back_populates="tasks")

    model_id = Column(String(36), ForeignKey("model.id"), nullable=True, index=True)
    model = relationship("Model", back_populates="tasks")

    def __repr__(self) -> str:
        """
        返回任务的字符串表示。

        返回:
            str: 任务的字符串表示，包含ID、名称和状态
        """
        return f"<Task(id={self.id}, name={self.name}, status={self.status})>"

    def to_dict(self) -> Dict[str, Any]:
        """
        将任务转换为字典表示。

        返回:
            Dict[str, Any]: 包含任务所有属性的字典
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "task_type": self.task_type,
            "status": self.status.value,
            "priority": self.priority,
            "celery_id": self.celery_id,
            "args": self.args,
            "kwargs": self.kwargs,
            "result": self.result,
            "error": self.error,
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "model_id": str(self.model_id) if self.model_id else None,
        }
