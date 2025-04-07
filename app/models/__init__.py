#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型包初始化

导入所有数据库模型，使它们对SQLAlchemy可见，并方便其他模块导入。
这样可以在一个地方导入所有模型，而不必在每个需要的地方单独导入。
"""

from app.models.user import User, UserRole
from app.models.api_key import APIKey
from app.models.model import Model, ModelVersion, ModelFramework, ModelStatus
from app.models.task import Task, TaskStatus, TaskPriority

# 在此处添加其他模型的导入
