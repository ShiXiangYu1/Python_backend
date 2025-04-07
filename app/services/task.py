#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务服务模块

提供任务的创建、查询、更新和删除等服务功能。
负责任务数据的持久化和业务逻辑处理。
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

from sqlalchemy import desc, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.celery import CeleryHelper
from app.models.task import Task, TaskStatus, TaskPriority
from app.services.base import CRUDBase
from app.services.redis_cache import redis_cache


class TaskService(CRUDBase):
    """
    任务服务类

    提供任务相关的业务逻辑实现，包括任务的创建、查询、更新和删除。
    与数据库和Celery队列交互，管理任务的生命周期。
    """

    def __init__(self):
        """初始化任务服务，设置模型为Task"""
        super().__init__(model=Task)

    async def create_task(
        self,
        db: AsyncSession,
        name: str,
        task_type: str,
        celery_task_name: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None,
        user_id: Optional[uuid.UUID] = None,
        model_id: Optional[uuid.UUID] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> Tuple[Task, str]:
        """
        创建任务

        创建一个新的任务记录，并提交到Celery队列执行。

        参数:
            db: 数据库会话
            name: 任务名称
            task_type: 任务类型，如"模型部署"、"模型训练"等
            celery_task_name: Celery任务函数名，如"app.tasks.model_tasks.deploy_model"
            args: 任务位置参数列表
            kwargs: 任务关键字参数字典
            user_id: 创建任务的用户ID
            model_id: 相关的模型ID
            priority: 任务优先级

        返回:
            Tuple[Task, str]: 创建的任务对象和Celery任务ID
        """
        # 创建任务记录
        task = Task(
            name=name,
            task_type=task_type,
            status=TaskStatus.PENDING,
            priority=priority.value if isinstance(priority, TaskPriority) else priority,
            args=args or [],
            kwargs=kwargs or {},
            user_id=user_id,
            model_id=model_id,
            created_at=datetime.utcnow(),
        )

        # 保存到数据库
        db.add(task)
        await db.commit()
        await db.refresh(task)

        # 将任务ID添加到参数中，以便任务可以更新状态
        if kwargs is None:
            kwargs = {}
        kwargs["task_id"] = str(task.id)

        # 根据优先级选择队列
        queue = "default"
        if isinstance(priority, TaskPriority):
            if priority == TaskPriority.HIGH:
                queue = "high_priority"
            elif priority == TaskPriority.LOW:
                queue = "low_priority"
        else:
            if priority >= TaskPriority.HIGH.value:
                queue = "high_priority"
            elif priority <= TaskPriority.LOW.value:
                queue = "low_priority"

        # 针对特定任务类型调整队列
        if task_type == "model_operation":
            queue = "model_operations"

        # 提交到Celery队列
        from app.core.celery import celery_app

        celery_task = celery_app.send_task(
            celery_task_name,
            args=args or [],
            kwargs=kwargs or {},
            queue=queue,
        )

        # 更新Celery任务ID
        task.celery_id = celery_task.id
        await db.commit()
        await db.refresh(task)

        # 缓存任务状态
        self._cache_task_status(task)

        return task, celery_task.id

    async def get_task(self, db: AsyncSession, task_id: uuid.UUID) -> Optional[Task]:
        """
        获取任务

        根据任务ID获取任务详细信息。优先从缓存获取，缓存不存在则从数据库获取。

        参数:
            db: 数据库会话
            task_id: 任务ID

        返回:
            Optional[Task]: 任务对象，如果不存在则返回None
        """
        # 尝试从缓存获取任务状态
        cached_task = self._get_cached_task(task_id)
        if cached_task:
            return cached_task

        # 缓存不存在，从数据库获取
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()

        # 如果任务存在，更新缓存
        if task:
            self._cache_task_status(task)

        return task

    async def get_tasks(
        self,
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        model_id: Optional[uuid.UUID] = None,
        status: Optional[Union[TaskStatus, str]] = None,
        task_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[Task]:
        """
        获取任务列表

        根据条件查询任务列表。

        参数:
            db: 数据库会话
            user_id: 过滤用户ID
            model_id: 过滤模型ID
            status: 过滤任务状态
            task_type: 过滤任务类型
            skip: 分页跳过数量
            limit: 分页限制数量
            order_by: 排序字段
            order_desc: 是否降序排序

        返回:
            List[Task]: 符合条件的任务列表
        """
        # 构建查询条件
        query = select(Task)
        filters = []

        if user_id:
            filters.append(Task.user_id == user_id)

        if model_id:
            filters.append(Task.model_id == model_id)

        if status:
            if isinstance(status, str):
                filters.append(Task.status == status)
            else:
                filters.append(Task.status == status)

        if task_type:
            filters.append(Task.task_type == task_type)

        if filters:
            query = query.where(and_(*filters))

        # 应用排序
        if order_by:
            column = getattr(Task, order_by, None)
            if column:
                query = query.order_by(desc(column) if order_desc else column)

        # 应用分页
        query = query.offset(skip).limit(limit)

        # 执行查询
        result = await db.execute(query)
        tasks = result.scalars().all()

        # 更新缓存
        for task in tasks:
            self._cache_task_status(task)

        return tasks

    async def update_task_status(
        self,
        db: AsyncSession,
        task_id: uuid.UUID,
        status: TaskStatus,
        progress: Optional[int] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[Task]:
        """
        更新任务状态

        更新任务的状态、进度和结果信息。

        参数:
            db: 数据库会话
            task_id: 任务ID
            status: 新的任务状态
            progress: 任务进度（0-100）
            result: 任务结果数据
            error: 任务错误信息

        返回:
            Optional[Task]: 更新后的任务对象，如果任务不存在则返回None
        """
        # 获取任务
        result_query = await db.execute(select(Task).where(Task.id == task_id))
        task = result_query.scalars().first()

        if not task:
            return None

        # 更新任务状态
        task.status = status

        # 更新任务进度
        if progress is not None:
            task.progress = progress

        # 更新任务结果
        if result is not None:
            task.result = result

        # 更新错误信息
        if error is not None:
            task.error = error

        # 如果状态变为运行中且开始时间未设置，设置开始时间
        if status == TaskStatus.RUNNING and not task.started_at:
            task.started_at = datetime.utcnow()

        # 如果状态变为终止状态且完成时间未设置，设置完成时间
        if (
            status in (TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.REVOKED)
            and not task.completed_at
        ):
            task.completed_at = datetime.utcnow()

        # 保存到数据库
        await db.commit()
        await db.refresh(task)

        # 更新缓存
        self._cache_task_status(task)

        return task

    async def cancel_task(self, db: AsyncSession, task_id: uuid.UUID) -> bool:
        """
        取消任务

        尝试取消一个正在执行的任务，并更新其状态为已取消。

        参数:
            db: 数据库会话
            task_id: 任务ID

        返回:
            bool: 是否成功取消任务
        """
        # 获取任务
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()

        if not task:
            return False

        # 如果任务已经处于终止状态，无法取消
        if task.status in (TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.REVOKED):
            return False

        # 尝试取消Celery任务
        if task.celery_id:
            from app.core.celery import celery_helper

            success = celery_helper.revoke_task(task.celery_id, terminate=True)

            if not success:
                return False

        # 更新任务状态为已取消
        task.status = TaskStatus.REVOKED
        task.completed_at = datetime.utcnow()

        # 保存到数据库
        await db.commit()
        await db.refresh(task)

        # 更新缓存
        self._cache_task_status(task)

        return True

    async def delete_task(self, db: AsyncSession, task_id: uuid.UUID) -> bool:
        """
        删除任务

        从数据库中删除任务记录。如果任务正在执行，会先尝试取消任务。

        参数:
            db: 数据库会话
            task_id: 任务ID

        返回:
            bool: 是否成功删除任务
        """
        # 获取任务
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()

        if not task:
            return False

        # 如果任务正在执行，先尝试取消
        if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            await self.cancel_task(db, task_id)

        # 删除任务记录
        await db.execute(Task.__table__.delete().where(Task.id == task_id))
        await db.commit()

        # 删除缓存
        redis_cache.invalidate_task_cache(str(task_id))

        return True

    async def sync_task_status_from_celery(
        self, db: AsyncSession, task_id: uuid.UUID
    ) -> Optional[Task]:
        """
        从Celery同步任务状态

        从Celery获取任务的最新状态，并更新数据库记录。

        参数:
            db: 数据库会话
            task_id: 任务ID

        返回:
            Optional[Task]: 更新后的任务对象，如果任务不存在则返回None
        """
        # 获取任务
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()

        if not task or not task.celery_id:
            return task

        # 从Celery获取任务状态
        from app.core.celery import celery_helper

        celery_task_info = celery_helper.get_task_info(task.celery_id)

        # 如果状态不同，更新任务状态
        if celery_task_info["status"] != task.status:
            status_mapping = {
                "PENDING": TaskStatus.PENDING,
                "STARTED": TaskStatus.RUNNING,
                "SUCCESS": TaskStatus.SUCCEEDED,
                "FAILURE": TaskStatus.FAILED,
                "REVOKED": TaskStatus.REVOKED,
            }

            new_status = status_mapping.get(celery_task_info["status"], task.status)

            # 更新进度
            progress = celery_task_info.get("progress", task.progress)

            # 更新结果
            result_data = celery_task_info.get("result", task.result)

            # 更新错误信息
            error = celery_task_info.get("error", task.error)

            # 更新任务状态
            return await self.update_task_status(
                db=db,
                task_id=task_id,
                status=new_status,
                progress=progress,
                result=result_data,
                error=error,
            )

        return task

    async def get_task_count(
        self,
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        model_id: Optional[uuid.UUID] = None,
        status: Optional[Union[TaskStatus, str]] = None,
    ) -> Dict[str, int]:
        """
        获取任务统计

        统计符合条件的任务数量，按状态分组。

        参数:
            db: 数据库会话
            user_id: 过滤用户ID
            model_id: 过滤模型ID
            status: 过滤任务状态

        返回:
            Dict[str, int]: 任务统计信息，包含各状态的任务数量和总数
        """
        # 准备过滤条件
        filters = []

        if user_id:
            filters.append(Task.user_id == user_id)

        if model_id:
            filters.append(Task.model_id == model_id)

        if status:
            if isinstance(status, str):
                filters.append(Task.status == status)
            else:
                filters.append(Task.status == status)

        # 获取总数
        total_query = select(func.count(Task.id))
        if filters:
            total_query = total_query.where(and_(*filters))

        result = await db.execute(total_query)
        total = result.scalar() or 0

        # 如果指定了状态，不需要按状态分组
        if status:
            return {
                "total": total,
                status.lower()
                if isinstance(status, str)
                else status.value.lower(): total,
            }

        # 按状态分组统计
        counts = {
            "total": total,
            "pending": 0,
            "running": 0,
            "succeeded": 0,
            "failed": 0,
            "revoked": 0,
        }

        # 如果总数为0，直接返回
        if total == 0:
            return counts

        # 获取各状态的数量
        for status_enum in TaskStatus:
            status_filters = filters.copy()
            status_filters.append(Task.status == status_enum)

            status_query = select(func.count(Task.id)).where(and_(*status_filters))
            result = await db.execute(status_query)
            count = result.scalar() or 0

            counts[status_enum.value.lower()] = count

        return counts

    def _cache_task_status(self, task: Task) -> bool:
        """
        缓存任务状态

        将任务状态信息缓存到Redis，提高查询性能。

        参数:
            task: 任务对象

        返回:
            bool: 缓存操作是否成功
        """
        # 将任务属性转换为字典
        task_data = {
            "id": str(task.id),
            "name": task.name,
            "task_type": task.task_type,
            "status": task.status.value
            if hasattr(task.status, "value")
            else task.status,
            "priority": task.priority,
            "progress": task.progress,
            "result": task.result,
            "error": task.error,
            "celery_id": task.celery_id,
            "user_id": str(task.user_id) if task.user_id else None,
            "model_id": str(task.model_id) if task.model_id else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat()
            if task.completed_at
            else None,
        }

        # 缓存任务状态
        return redis_cache.cache_task_status(str(task.id), task_data)

    def _get_cached_task(self, task_id: uuid.UUID) -> Optional[Task]:
        """
        获取缓存的任务

        从缓存中获取任务状态信息，并转换为Task对象。

        参数:
            task_id: 任务ID

        返回:
            Optional[Task]: 任务对象，如果缓存不存在则返回None
        """
        # 从缓存获取任务状态
        task_data = redis_cache.get_task_status(str(task_id))

        if not task_data:
            return None

        # 转换为Task对象
        try:
            task = Task()
            task.id = uuid.UUID(task_data["id"])
            task.name = task_data["name"]
            task.task_type = task_data["task_type"]
            task.status = (
                TaskStatus(task_data["status"]) if task_data["status"] else None
            )
            task.priority = (
                int(task_data["priority"]) if task_data["priority"] else None
            )
            task.progress = int(task_data["progress"]) if task_data["progress"] else 0
            task.result = task_data["result"]
            task.error = task_data["error"]
            task.celery_id = task_data["celery_id"]
            task.user_id = (
                uuid.UUID(task_data["user_id"]) if task_data["user_id"] else None
            )
            task.model_id = (
                uuid.UUID(task_data["model_id"]) if task_data["model_id"] else None
            )

            if task_data["created_at"]:
                task.created_at = datetime.fromisoformat(task_data["created_at"])
            if task_data["started_at"]:
                task.started_at = datetime.fromisoformat(task_data["started_at"])
            if task_data["completed_at"]:
                task.completed_at = datetime.fromisoformat(task_data["completed_at"])

            return task
        except Exception as e:
            import logging

            logging.error(f"从缓存还原任务对象失败: {e}")
            return None


# 导出服务实例
task_service = TaskService()
