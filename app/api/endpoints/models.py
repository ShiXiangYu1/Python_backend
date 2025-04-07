#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型API模块

处理AI模型管理相关的API端点，如模型上传、部署、查询等。
提供模型资源的完整生命周期管理。
"""

from typing import Dict, List, Any, Optional
from typing_extensions import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.models.model import ModelStatus
from app.schemas.common import Message, Page, PaginationParams
from app.schemas.model import (
    Model,
    ModelCreate,
    ModelUpdate,
    ModelDeploy,
    ModelVersion,
    ModelVersionCreate,
    ModelVersionUpdate,
)
from app.services.model import model_service, model_version_service
from app.utils.cache import cache, invalidate_cache


# 创建路由器
router = APIRouter()


# 模型相关端点
@router.post("", response_model=Model)
@invalidate_cache(prefix="model:")
async def create_model(
    model_in: ModelCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Model:
    """
    创建模型

    创建新的AI模型元数据。

    参数:
        model_in: 模型创建数据
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        Model: 创建的模型信息
    """
    # 创建模型
    model = await model_service.create_with_owner(
        db, obj_in=model_in, owner_id=str(current_user.id)
    )
    return model


@router.get("", response_model=Page[Model])
@cache(expire=300, key_prefix="model:list:", vary_on_headers=["Authorization"])
async def read_models(
    pagination: Annotated[PaginationParams, Depends()],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    public_only: bool = False,
) -> Page[Model]:
    """
    获取模型列表

    返回分页的模型列表，包括用户自己的模型和公开模型。

    参数:
        pagination: 分页参数
        current_user: 当前登录用户
        db: 数据库会话
        public_only: 是否只返回公开模型

    返回:
        Page[Model]: 分页的模型列表
    """
    # 计算分页参数
    skip = (pagination.page - 1) * pagination.page_size

    # 获取模型列表和总数
    owner_id = None if public_only else str(current_user.id)
    models, total = await model_service.get_models_with_pagination(
        db,
        owner_id=owner_id,
        skip=skip,
        limit=pagination.page_size,
        public_only=public_only,
    )

    # 构建分页响应
    return Page.create(
        items=models, total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.get("/public", response_model=Page[Model])
@cache(expire=600, key_prefix="model:public:", vary_on_headers=[])
async def read_public_models(
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Page[Model]:
    """
    获取公开模型列表

    返回分页的公开模型列表，无需登录即可访问。

    参数:
        pagination: 分页参数
        db: 数据库会话

    返回:
        Page[Model]: 分页的公开模型列表
    """
    # 计算分页参数
    skip = (pagination.page - 1) * pagination.page_size

    # 获取公开模型列表和总数
    models, total = await model_service.get_models_with_pagination(
        db, owner_id=None, skip=skip, limit=pagination.page_size, public_only=True
    )

    # 构建分页响应
    return Page.create(
        items=models, total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.get("/{model_id}", response_model=Model)
@cache(expire=60, key_prefix="model:detail:")
async def read_model(
    model_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Model:
    """
    获取模型

    返回特定模型的信息。

    参数:
        model_id: 模型ID
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        Model: 模型信息

    异常:
        HTTPException: 模型不存在或无权访问时抛出
    """
    # 获取模型
    model = await model_service.get(db, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    # 检查访问权限：只有模型所有者或公开模型可以访问
    if model.owner_id != str(current_user.id) and not model.is_public:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该模型")

    return model


@router.put("/{model_id}", response_model=Model)
async def update_model(
    model_id: str,
    model_in: ModelUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Model:
    """
    更新模型

    更新模型的信息。

    参数:
        model_id: 模型ID
        model_in: 模型更新数据
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        Model: 更新后的模型信息

    异常:
        HTTPException: 模型不存在或无权访问时抛出
    """
    # 获取模型
    model = await model_service.get(db, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    # 检查访问权限：只有模型所有者可以更新
    if model.owner_id != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权更新该模型")

    # 更新模型
    updated_model = await model_service.update(db, db_obj=model, obj_in=model_in)
    return updated_model


@router.delete("/{model_id}", response_model=Message)
async def delete_model(
    model_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Message:
    """
    删除模型

    删除模型及其所有版本和文件。

    参数:
        model_id: 模型ID
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        Message: 操作结果消息

    异常:
        HTTPException: 模型不存在或无权访问时抛出
    """
    # 获取模型
    model = await model_service.get(db, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    # 检查访问权限：只有模型所有者可以删除
    if model.owner_id != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该模型")

    # TODO: 删除模型的所有版本和文件

    # 删除模型
    await model_service.remove(db, id=model_id)

    return Message(detail="模型已成功删除")


@router.post("/{model_id}/upload", response_model=Model)
async def upload_model_file(
    model_id: str,
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Model:
    """
    上传模型文件

    上传模型文件并更新模型信息。

    参数:
        model_id: 模型ID
        file: 上传的文件
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        Model: 更新后的模型信息

    异常:
        HTTPException: 模型不存在、无权访问或上传失败时抛出
    """
    # 获取模型
    model = await model_service.get(db, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    # 检查访问权限：只有模型所有者可以上传
    if model.owner_id != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权上传到该模型")

    # 上传模型文件
    updated_model = await model_service.upload_model_file(
        db, model_id=model_id, file=file
    )
    if updated_model is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="上传模型文件失败"
        )

    return updated_model


@router.post("/{model_id}/deploy", response_model=Model)
async def deploy_model(
    model_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    deploy_config: Optional[ModelDeploy] = None,
    background_tasks: BackgroundTasks = None,
) -> Model:
    """
    部署模型

    将模型部署为API服务。

    参数:
        model_id: 模型ID
        current_user: 当前登录用户
        db: 数据库会话
        deploy_config: 部署配置
        background_tasks: 后台任务

    返回:
        Model: 更新后的模型信息

    异常:
        HTTPException: 模型不存在、无权访问或部署失败时抛出
    """
    # 获取模型
    model = await model_service.get(db, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    # 检查访问权限：只有模型所有者可以部署
    if model.owner_id != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权部署该模型")

    # 检查模型状态：只有已上传、有效或未部署的模型可以部署
    if model.status not in [
        ModelStatus.UPLOADED,
        ModelStatus.VALID,
        ModelStatus.UNDEPLOYED,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前模型状态({model.status})不允许部署",
        )

    # 部署配置
    config = deploy_config.config if deploy_config else {}

    # 部署模型
    updated_model = await model_service.deploy_model(
        db, model_id=model_id, config=config
    )
    if updated_model is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="部署模型失败"
        )

    return updated_model


# 模型版本相关端点
@router.post("/{model_id}/versions", response_model=ModelVersion)
async def create_model_version(
    model_id: str,
    version_in: ModelVersionCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ModelVersion:
    """
    创建模型版本

    为特定模型创建新版本。

    参数:
        model_id: 模型ID
        version_in: 版本创建数据
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        ModelVersion: 创建的版本信息

    异常:
        HTTPException: 模型不存在或无权访问时抛出
    """
    # 获取模型
    model = await model_service.get(db, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    # 检查访问权限：只有模型所有者可以创建版本
    if model.owner_id != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权为该模型创建版本")

    # 创建模型版本
    version = await model_version_service.create_with_model(
        db, obj_in=version_in, parent_model_id=model_id
    )
    return version


@router.get("/{model_id}/versions", response_model=List[ModelVersion])
@cache(expire=60, key_prefix="model:versions:")
async def read_model_versions(
    model_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> List[ModelVersion]:
    """
    获取模型版本列表

    返回特定模型的所有版本。

    参数:
        model_id: 模型ID
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        List[ModelVersion]: 版本列表

    异常:
        HTTPException: 模型不存在或无权访问时抛出
    """
    # 获取模型
    model = await model_service.get(db, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    # 检查访问权限：只有模型所有者或公开模型可以查看版本
    if model.owner_id != str(current_user.id) and not model.is_public:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该模型的版本")

    # 获取版本列表
    versions = await model_version_service.get_multi_by_model(
        db, parent_model_id=model_id
    )
    return versions


@router.get("/{model_id}/versions/{version_id}", response_model=ModelVersion)
async def read_model_version(
    model_id: str,
    version_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ModelVersion:
    """
    获取模型版本

    返回特定模型版本的信息。

    参数:
        model_id: 模型ID
        version_id: 版本ID
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        ModelVersion: 版本信息

    异常:
        HTTPException: 模型或版本不存在或无权访问时抛出
    """
    # 获取模型
    model = await model_service.get(db, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    # 检查访问权限：只有模型所有者或公开模型可以查看版本
    if model.owner_id != str(current_user.id) and not model.is_public:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该模型的版本")

    # 获取版本
    version = await model_version_service.get(db, version_id)
    if version is None or version.parent_model_id != model_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在")

    return version


@router.post(
    "/{model_id}/versions/{version_id}/set-current", response_model=ModelVersion
)
async def set_current_version(
    model_id: str,
    version_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ModelVersion:
    """
    设置当前版本

    将特定版本设置为模型的当前版本。

    参数:
        model_id: 模型ID
        version_id: 版本ID
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        ModelVersion: 更新后的版本信息

    异常:
        HTTPException: 模型或版本不存在或无权访问时抛出
    """
    # 获取模型
    model = await model_service.get(db, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    # 检查访问权限：只有模型所有者可以设置当前版本
    if model.owner_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权设置该模型的当前版本"
        )

    # 获取版本
    version = await model_version_service.get(db, version_id)
    if version is None or version.parent_model_id != model_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在")

    # 设置当前版本
    updated_version = await model_version_service.set_current_version(
        db, version_id=version_id, parent_model_id=model_id
    )
    if updated_version is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="设置当前版本失败"
        )

    return updated_version


@router.delete("/{model_id}/versions/{version_id}", response_model=Message)
async def delete_model_version(
    model_id: str,
    version_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Message:
    """
    删除模型版本

    删除特定模型版本及其文件。

    参数:
        model_id: 模型ID
        version_id: 版本ID
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        Message: 操作结果消息

    异常:
        HTTPException: 模型或版本不存在或无权访问时抛出
    """
    # 获取模型
    model = await model_service.get(db, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")

    # 检查访问权限：只有模型所有者可以删除版本
    if model.owner_id != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该模型的版本")

    # 获取版本
    version = await model_version_service.get(db, version_id)
    if version is None or version.parent_model_id != model_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在")

    # 不能删除当前版本
    if version.is_current:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除当前版本")

    # TODO: 删除版本文件

    # 删除版本
    await model_version_service.remove(db, id=version_id)

    return Message(detail="模型版本已成功删除")
