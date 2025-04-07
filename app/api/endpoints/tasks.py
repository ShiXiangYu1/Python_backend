#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务API端点模块

提供任务相关的API端点，包括任务的创建、查询、更新、取消和删除功能。
支持任务优先级管理、状态和进度跟踪，以及任务结果的存储和检索。

主要功能：
1. 任务创建与提交到异步队列
2. 任务状态查询与进度跟踪
3. 任务执行结果获取
4. 任务取消与终止
5. 任务统计与管理
"""

import uuid
from typing import List, Optional, Any, Dict

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Path,
    Body,
    BackgroundTasks,
)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.deps import get_db, get_current_user, get_current_active_user
from app.core.celery import CeleryHelper
from app.models.user import User
from app.models.task import TaskStatus
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskQuery,
    TaskCountResponse,
)
from app.services.task import TaskService


router = APIRouter()
task_service = TaskService()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    *,
    db: AsyncSession = Depends(get_db),
    task_create: TaskCreate = Body(...),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    创建任务

    创建一个新的异步任务，并提交到任务队列执行。该接口会返回任务的元数据，但任务将在后台异步执行。

    参数:
    - **task_create**: 任务创建参数
        - **name**: 任务名称，用于标识和显示
        - **task_type**: 任务类型，用于分类和筛选任务
        - **celery_task_name**: Celery任务函数名，必须是已注册的Celery任务
        - **args**: 任务位置参数列表，传递给Celery任务函数(可选)
        - **kwargs**: 任务关键字参数字典，传递给Celery任务函数(可选)
        - **priority**: 任务优先级，影响任务执行顺序，可选值：HIGH, NORMAL, LOW(默认: NORMAL)
        - **model_id**: 关联的模型ID，如果任务与特定模型相关(可选)
        - **user_id**: 任务所有者ID，默认为当前用户(可选)

    返回:
        TaskResponse: 创建的任务信息，包含任务ID、状态、创建时间等元数据

    异常:
        HTTPException 400: 创建任务失败时返回，可能原因包括无效的任务名称、类型或Celery任务不存在

    示例:
        ```json
        {
          "name": "模型训练任务",
          "task_type": "model_training",
          "celery_task_name": "app.tasks.model_tasks.train_model",
          "args": [42, "param1"],
          "kwargs": {"epochs": 10, "batch_size": 32},
          "priority": "HIGH",
          "model_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        }
        ```
    """
    # 如果用户ID未指定，使用当前用户ID
    if not task_create.user_id:
        task_create.user_id = current_user.id

    try:
        # 创建任务
        task, celery_id = await task_service.create_task(
            db=db,
            name=task_create.name,
            task_type=task_create.task_type,
            celery_task_name=task_create.celery_task_name,
            args=task_create.args,
            kwargs=task_create.kwargs,
            user_id=task_create.user_id,
            model_id=task_create.model_id,
            priority=task_create.priority,
        )
        return task
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"创建任务失败: {str(e)}"
        )


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[uuid.UUID] = Query(None, description="过滤用户ID"),
    model_id: Optional[uuid.UUID] = Query(None, description="过滤模型ID"),
    status: Optional[str] = Query(None, description="过滤任务状态"),
    task_type: Optional[str] = Query(None, description="过滤任务类型"),
    skip: int = Query(0, ge=0, description="分页跳过数量"),
    limit: int = Query(100, ge=1, le=500, description="分页限制数量"),
    order_by: str = Query("created_at", description="排序字段"),
    order_desc: bool = Query(True, description="是否降序排序"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取任务列表

    根据条件查询任务列表，支持分页、排序和多种过滤条件。非管理员用户只能查看自己的任务。

    参数:
    - **user_id**: 过滤用户ID，仅返回指定用户的任务(管理员可用，可选)
    - **model_id**: 过滤模型ID，仅返回与特定模型关联的任务(可选)
    - **status**: 过滤任务状态，可选值：PENDING, RUNNING, SUCCEEDED, FAILED, REVOKED(可选)
    - **task_type**: 过滤任务类型，如 model_training, model_inference 等(可选)
    - **skip**: 分页跳过数量，用于分页控制(默认: 0)
    - **limit**: 分页限制数量，每页返回的最大记录数(默认: 100，最大: 500)
    - **order_by**: 排序字段，支持 created_at, status, progress, priority 等(默认: created_at)
    - **order_desc**: 是否降序排序，true表示降序，false表示升序(默认: true)

    返回:
        List[TaskResponse]: 任务列表，每个任务包含ID、名称、状态、进度、创建时间等信息

    异常:
        HTTPException 403: 非管理员尝试查看不属于自己的任务时返回

    注意:
        任务列表仅返回任务元数据，不包含完整的任务结果数据
    """
    # 非管理员只能查看自己的任务
    if not current_user.is_admin:
        user_id = current_user.id

    tasks = await task_service.get_tasks(
        db=db,
        user_id=user_id,
        model_id=model_id,
        status=status,
        task_type=task_type,
        skip=skip,
        limit=limit,
        order_by=order_by,
        order_desc=order_desc,
    )
    return tasks


@router.get("/count", response_model=TaskCountResponse)
async def get_task_count(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[uuid.UUID] = Query(None, description="过滤用户ID"),
    model_id: Optional[uuid.UUID] = Query(None, description="过滤模型ID"),
    status: Optional[str] = Query(None, description="过滤任务状态"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取任务统计

    统计不同状态的任务数量，支持按用户、模型和状态筛选。返回每种状态的任务数量以及总数。
    非管理员用户只能获取自己任务的统计信息。

    参数:
    - **user_id**: 过滤用户ID，仅统计指定用户的任务(管理员可用，可选)
    - **model_id**: 过滤模型ID，仅统计与特定模型关联的任务(可选)
    - **status**: 过滤任务状态，仅统计特定状态的任务(可选)

    返回:
        TaskCountResponse: 任务统计信息，包含以下字段：
        - **total**: 符合条件的任务总数
        - **pending**: 等待中的任务数量
        - **running**: 运行中的任务数量
        - **succeeded**: 已成功的任务数量
        - **failed**: 已失败的任务数量
        - **revoked**: 已取消的任务数量

    异常:
        HTTPException 403: 非管理员尝试统计不属于自己的任务时返回

    示例响应:
        ```json
        {
          "total": 42,
          "pending": 5,
          "running": 3,
          "succeeded": 30,
          "failed": 2,
          "revoked": 2
        }
        ```
    """
    # 非管理员只能查看自己的任务统计
    if not current_user.is_admin:
        user_id = current_user.id

    counts = await task_service.get_task_count(
        db=db,
        user_id=user_id,
        model_id=model_id,
        status=status,
    )
    return counts


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    *,
    db: AsyncSession = Depends(get_db),
    task_id: uuid.UUID = Path(..., description="任务ID"),
    sync_status: bool = Query(False, description="是否从Celery同步最新状态"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取任务详情

    根据任务ID获取任务的详细信息，包括任务状态、进度、结果和错误信息等。
    可选择是否从Celery同步最新状态，非任务所有者需要管理员权限才能访问。

    参数:
    - **task_id**: 任务ID，UUID格式
    - **sync_status**: 是否从Celery同步最新状态，设为true将从Celery获取最新状态并更新数据库(默认: false)

    返回:
        TaskResponse: 任务详情，包含以下主要字段：
        - **id**: 任务唯一标识符
        - **name**: 任务名称
        - **task_type**: 任务类型
        - **status**: 任务当前状态
        - **priority**: 任务优先级
        - **progress**: 任务执行进度(0-100)
        - **result**: 任务执行结果
        - **error**: 错误信息(如果失败)
        - **created_at**: 创建时间
        - **started_at**: 开始执行时间
        - **completed_at**: 完成时间
        - **celery_id**: Celery任务ID
        - **user_id**: 任务所有者ID
        - **model_id**: 关联的模型ID

    异常:
        HTTPException 404: 任务不存在时返回
        HTTPException 403: 非管理员尝试访问不属于自己的任务时返回
    """
    # 获取任务
    if sync_status:
        task = await task_service.sync_task_status_from_celery(db, task_id)
    else:
        task = await task_service.get_task(db, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"任务不存在: {task_id}"
        )

    # 非管理员只能查看自己的任务
    if not current_user.is_admin and task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限访问此任务")

    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    *,
    db: AsyncSession = Depends(get_db),
    task_id: uuid.UUID = Path(..., description="任务ID"),
    task_update: TaskUpdate = Body(...),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    更新任务

    更新任务的状态、进度、结果和错误信息。主要用于任务执行过程中更新进度和状态，
    或者在任务完成后更新结果。非任务所有者需要管理员权限才能更新。

    参数:
    - **task_id**: 任务ID，UUID格式
    - **task_update**: 任务更新参数，包含以下可选字段：
        - **status**: 任务状态，可选值：PENDING, RUNNING, SUCCEEDED, FAILED, REVOKED
        - **progress**: 任务进度，0-100之间的整数
        - **result**: 任务结果，任意JSON可序列化的数据结构
        - **error**: 任务错误信息，通常在任务失败时设置

    返回:
        TaskResponse: 更新后的任务信息，包含所有任务字段

    异常:
        HTTPException 404: 任务不存在时返回
        HTTPException 403: 非管理员尝试更新不属于自己的任务时返回
        HTTPException 400: 任务状态值无效时返回

    注意:
        此接口通常由系统内部调用，用于更新任务执行过程中的状态和进度
    """
    # 获取任务
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"任务不存在: {task_id}"
        )

    # 非管理员只能更新自己的任务
    if not current_user.is_admin and task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限更新此任务")

    # 将字符串状态转换为枚举
    status_value = None
    if task_update.status:
        try:
            status_value = TaskStatus(task_update.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的任务状态: {task_update.status}",
            )

    # 更新任务
    updated_task = await task_service.update_task_status(
        db=db,
        task_id=task_id,
        status=status_value if status_value else task.status,
        progress=task_update.progress,
        result=task_update.result,
        error=task_update.error,
    )

    return updated_task


@router.post("/{task_id}/cancel", response_model=Dict[str, Any])
async def cancel_task(
    *,
    db: AsyncSession = Depends(get_db),
    task_id: uuid.UUID = Path(..., description="任务ID"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    取消任务

    尝试取消一个正在执行或等待中的任务。取消操作会向Celery发送任务撤销信号，
    并将任务状态更新为已取消(REVOKED)。已完成、已失败或已取消的任务不能被取消。
    非任务所有者需要管理员权限才能取消。

    参数:
    - **task_id**: 任务ID，UUID格式

    返回:
        Dict[str, Any]: 取消操作的结果，包含以下字段：
        - **success**: 布尔值，表示操作是否成功
        - **message**: 操作结果的描述信息

    异常:
        HTTPException 404: 任务不存在时返回
        HTTPException 403: 非管理员尝试取消不属于自己的任务时返回

    示例响应:
        ```json
        {
          "success": true,
          "message": "任务取消成功"
        }
        ```

    注意:
        对于长时间运行的任务，取消可能需要一段时间才能生效，
        取决于任务的实现方式和当前执行状态
    """
    # 获取任务
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"任务不存在: {task_id}"
        )

    # 非管理员只能取消自己的任务
    if not current_user.is_admin and task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限取消此任务")

    # 检查任务是否可以取消
    if task.status in (TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.REVOKED):
        return {"success": False, "message": f"任务已经处于终态: {task.status}，无法取消"}

    # 取消任务
    success = await task_service.cancel_task(db, task_id)

    if success:
        return {"success": True, "message": "任务取消成功"}
    else:
        return {"success": False, "message": "任务取消失败，可能任务已经完成或不存在"}


@router.delete("/{task_id}", response_model=Dict[str, Any])
async def delete_task(
    *,
    db: AsyncSession = Depends(get_db),
    task_id: uuid.UUID = Path(..., description="任务ID"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    删除任务

    从数据库中删除一个任务记录。如果任务正在执行，会先尝试取消任务，然后删除记录。
    删除操作是永久性的，任务的所有相关数据都将被删除。非任务所有者需要管理员权限才能删除。

    参数:
    - **task_id**: 任务ID，UUID格式

    返回:
        Dict[str, Any]: 删除操作的结果，包含以下字段：
        - **success**: 布尔值，表示操作是否成功
        - **message**: 操作结果的描述信息

    异常:
        HTTPException 404: 任务不存在时返回
        HTTPException 403: 非管理员尝试删除不属于自己的任务时返回

    示例响应:
        ```json
        {
          "success": true,
          "message": "任务删除成功"
        }
        ```

    注意:
        删除任务不会删除任务可能产生的外部资源，如文件、数据库记录等，
        这些需要在任务实现中自行处理
    """
    # 获取任务
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"任务不存在: {task_id}"
        )

    # 非管理员只能删除自己的任务
    if not current_user.is_admin and task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限删除此任务")

    # 删除任务
    success = await task_service.delete_task(db, task_id)

    if success:
        return {"success": True, "message": "任务删除成功"}
    else:
        return {"success": False, "message": "任务删除失败"}
