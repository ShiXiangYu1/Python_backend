#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库集成模块

导入所有模型和基类，用于数据库迁移和初始化。
这个模块主要被Alembic用于数据库迁移。
"""

# 导入所有模型，使其对Alembic可见
from app.db.base_class import BaseModel
from app.models.user import User, UserRole
from app.models.api_key import APIKey
from app.models.model import Model, ModelVersion, ModelFramework, ModelStatus
from app.models.task import Task, TaskStatus, TaskPriority

# 在此处添加其他模型的导入 