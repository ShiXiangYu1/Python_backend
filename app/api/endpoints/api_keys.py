#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API密钥API模块

处理API密钥管理相关的API端点，如创建密钥、获取密钥列表、撤销密钥等。
用于管理API访问凭据，支持程序化访问系统功能。
"""

from typing_extensions import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.api_key import APIKey, APIKeyCreate, APIKeyCreated, APIKeyUpdate
from app.schemas.common import Message, Page, PaginationParams
from app.services.api_key import api_key_service


# 创建路由器
router = APIRouter()


@router.post("", response_model=APIKeyCreated)
async def create_api_key(
    api_key_in: APIKeyCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> APIKey:
    """
    创建API密钥
    
    为当前用户创建新的API密钥。
    
    参数:
        api_key_in: API密钥创建数据
        current_user: 当前登录用户
        db: 数据库会话
        
    返回:
        APIKeyCreated: 创建的API密钥信息
    """
    # 创建API密钥
    api_key = await api_key_service.create_with_user(
        db, obj_in=api_key_in, user_id=str(current_user.id)
    )
    return api_key


@router.get("", response_model=Page[APIKey])
async def read_api_keys(
    pagination: Annotated[PaginationParams, Depends()],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Page[APIKey]:
    """
    获取API密钥列表
    
    返回当前用户的API密钥列表。
    
    参数:
        pagination: 分页参数
        current_user: 当前登录用户
        db: 数据库会话
        
    返回:
        Page[APIKey]: 分页的API密钥列表
    """
    # 计算分页参数
    skip = (pagination.page - 1) * pagination.page_size
    
    # 获取API密钥列表和总数
    api_keys, total = await api_key_service.get_api_keys_with_pagination(
        db, user_id=str(current_user.id), skip=skip, limit=pagination.page_size
    )
    
    # 构建分页响应
    return Page.create(
        items=api_keys,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get("/{api_key_id}", response_model=APIKey)
async def read_api_key(
    api_key_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> APIKey:
    """
    获取API密钥
    
    返回特定API密钥的信息。
    
    参数:
        api_key_id: API密钥ID
        current_user: 当前登录用户
        db: 数据库会话
        
    返回:
        APIKey: API密钥信息
        
    异常:
        HTTPException: API密钥不存在或不属于当前用户时抛出
    """
    # 获取API密钥
    api_key = await api_key_service.get(db, api_key_id)
    if api_key is None or api_key.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    return api_key


@router.put("/{api_key_id}", response_model=APIKey)
async def update_api_key(
    api_key_id: str,
    api_key_in: APIKeyUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> APIKey:
    """
    更新API密钥
    
    更新API密钥的信息。
    
    参数:
        api_key_id: API密钥ID
        api_key_in: API密钥更新数据
        current_user: 当前登录用户
        db: 数据库会话
        
    返回:
        APIKey: 更新后的API密钥信息
        
    异常:
        HTTPException: API密钥不存在或不属于当前用户时抛出
    """
    # 获取API密钥
    api_key = await api_key_service.get(db, api_key_id)
    if api_key is None or api_key.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    # 更新API密钥
    updated_api_key = await api_key_service.update(db, db_obj=api_key, obj_in=api_key_in)
    return updated_api_key


@router.delete("/{api_key_id}", response_model=Message)
async def delete_api_key(
    api_key_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Message:
    """
    删除API密钥
    
    删除API密钥。
    
    参数:
        api_key_id: API密钥ID
        current_user: 当前登录用户
        db: 数据库会话
        
    返回:
        Message: 操作结果消息
        
    异常:
        HTTPException: API密钥不存在或不属于当前用户时抛出
    """
    # 获取API密钥
    api_key = await api_key_service.get(db, api_key_id)
    if api_key is None or api_key.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    # 删除API密钥
    await api_key_service.remove(db, id=api_key_id)
    
    return Message(detail="API密钥已成功删除")


@router.post("/{api_key_id}/deactivate", response_model=APIKey)
async def deactivate_api_key(
    api_key_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> APIKey:
    """
    停用API密钥
    
    将API密钥设置为非激活状态。
    
    参数:
        api_key_id: API密钥ID
        current_user: 当前登录用户
        db: 数据库会话
        
    返回:
        APIKey: 更新后的API密钥信息
        
    异常:
        HTTPException: API密钥不存在或不属于当前用户时抛出
    """
    # 获取API密钥
    api_key = await api_key_service.get(db, api_key_id)
    if api_key is None or api_key.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    # 停用API密钥
    deactivated_api_key = await api_key_service.deactivate(db, id=api_key_id)
    if deactivated_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停用API密钥失败"
        )
    
    return deactivated_api_key 