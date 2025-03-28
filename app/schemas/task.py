#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务模式模块

定义任务相关的Pydantic模型，用于API请求和响应的数据验证和序列化。
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field, UUID4

from app.models.task import TaskStatus, TaskPriority


# 基础任务模型
class TaskBase(BaseModel):
    """
    基础任务模型
    
    定义任务的基本属性，作为其他任务相关模型的基类。
    """
    name: str = Field(..., description="任务名称")
    task_type: str = Field(..., description="任务类型，如'model_deploy'、'model_train'等")
    priority: int = Field(TaskPriority.NORMAL, description="任务优先级，数值越大优先级越高")


# 创建任务请求模型
class TaskCreate(TaskBase):
    """
    创建任务请求模型
    
    用于验证创建任务API的请求数据。
    """
    celery_task_name: str = Field(..., description="Celery任务函数名，如'app.tasks.model_tasks.deploy_model'")
    args: Optional[List[Any]] = Field(default=None, description="任务位置参数")
    kwargs: Optional[Dict[str, Any]] = Field(default=None, description="任务关键字参数")
    user_id: Optional[UUID4] = Field(default=None, description="关联的用户ID")
    model_id: Optional[UUID4] = Field(default=None, description="关联的模型ID")
    
    class Config:
        """配置类"""
        schema_extra = {
            "example": {
                "name": "部署模型 ResNet50",
                "task_type": "model_deploy",
                "celery_task_name": "app.tasks.model_tasks.deploy_model",
                "args": [],
                "kwargs": {"model_name": "resnet50", "batch_size": 32},
                "priority": 2,
                "model_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
            }
        }


# 更新任务请求模型
class TaskUpdate(BaseModel):
    """
    更新任务请求模型
    
    用于验证更新任务API的请求数据。
    """
    status: Optional[str] = Field(default=None, description="任务状态")
    progress: Optional[int] = Field(default=None, ge=0, le=100, description="任务进度，0-100的整数")
    result: Optional[Dict[str, Any]] = Field(default=None, description="任务结果")
    error: Optional[str] = Field(default=None, description="任务错误信息")
    
    class Config:
        """配置类"""
        schema_extra = {
            "example": {
                "status": "running",
                "progress": 50,
                "result": {"accuracy": 0.95},
                "error": None
            }
        }


# 任务查询参数模型
class TaskQuery(BaseModel):
    """
    任务查询参数模型
    
    用于验证任务列表查询API的请求参数。
    """
    user_id: Optional[UUID4] = Field(default=None, description="过滤用户ID")
    model_id: Optional[UUID4] = Field(default=None, description="过滤模型ID")
    status: Optional[str] = Field(default=None, description="过滤任务状态")
    task_type: Optional[str] = Field(default=None, description="过滤任务类型")
    skip: int = Field(0, ge=0, description="分页跳过数量")
    limit: int = Field(100, ge=1, le=500, description="分页限制数量")
    order_by: str = Field("created_at", description="排序字段")
    order_desc: bool = Field(True, description="是否降序排序")
    
    class Config:
        """配置类"""
        schema_extra = {
            "example": {
                "status": "pending",
                "task_type": "model_deploy",
                "skip": 0,
                "limit": 10,
                "order_by": "created_at",
                "order_desc": True
            }
        }


# 任务响应模型
class TaskResponse(TaskBase):
    """
    任务响应模型
    
    用于序列化任务API的响应数据。
    """
    id: UUID4 = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    celery_id: Optional[str] = Field(default=None, description="Celery任务ID")
    progress: int = Field(..., description="任务进度，0-100的整数")
    result: Optional[Dict[str, Any]] = Field(default=None, description="任务结果")
    error: Optional[str] = Field(default=None, description="任务错误信息")
    created_at: datetime = Field(..., description="任务创建时间")
    started_at: Optional[datetime] = Field(default=None, description="任务开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="任务完成时间")
    user_id: Optional[UUID4] = Field(default=None, description="关联的用户ID")
    model_id: Optional[UUID4] = Field(default=None, description="关联的模型ID")
    
    class Config:
        """配置类"""
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "name": "部署模型 ResNet50",
                "task_type": "model_deploy",
                "status": "running",
                "priority": 2,
                "celery_id": "c8535959-4e5e-435d-a8fb-58a673b21448",
                "progress": 50,
                "result": None,
                "error": None,
                "created_at": "2023-01-01T12:00:00Z",
                "started_at": "2023-01-01T12:01:00Z",
                "completed_at": None,
                "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "model_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
            }
        }


# 任务统计响应模型
class TaskCountResponse(BaseModel):
    """
    任务统计响应模型
    
    用于序列化任务统计API的响应数据。
    """
    total: int = Field(..., description="任务总数")
    pending: int = Field(..., description="待处理任务数")
    running: int = Field(..., description="执行中任务数")
    succeeded: int = Field(..., description="已成功任务数")
    failed: int = Field(..., description="已失败任务数")
    revoked: int = Field(..., description="已取消任务数")
    
    class Config:
        """配置类"""
        schema_extra = {
            "example": {
                "total": 100,
                "pending": 10,
                "running": 5,
                "succeeded": 80,
                "failed": 3,
                "revoked": 2
            }
        } 