#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户API模块

处理用户管理相关的API端点，如获取用户列表、创建用户、更新用户信息等。
提供用户资源的CRUD操作接口。
"""

from typing_extensions import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_admin_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.common import Message, Page, PaginationParams
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate, UserList
from app.services.user import user_service


# 创建路由器
router = APIRouter()


@router.get("/me", response_model=UserSchema)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    获取当前用户信息

    返回当前登录用户的信息。

    参数:
        current_user: 当前登录用户

    返回:
        User: 当前用户信息
    """
    return current_user


@router.put("/me", response_model=UserSchema)
async def update_user_me(
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    更新当前用户信息

    允许用户更新自己的信息，但不允许修改角色。

    参数:
        user_in: 用户更新数据
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        User: 更新后的用户信息

    异常:
        HTTPException: 用户名或邮箱已存在时抛出
    """
    # 用户不能修改自己的角色
    if user_in.role is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="不允许修改自己的角色"
        )

    # 检查用户名是否已存在
    if user_in.username and user_in.username != current_user.username:
        existing_user = await user_service.get_by_username(
            db, username=user_in.username
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在"
            )

    # 检查邮箱是否已存在
    if user_in.email and user_in.email != current_user.email:
        existing_email = await user_service.get_by_email(db, email=user_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被注册"
            )

    # 更新用户信息
    user = await user_service.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.get("", response_model=Page[UserSchema])
async def read_users(
    pagination: Annotated[PaginationParams, Depends()],
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Page[UserSchema]:
    """
    获取用户列表

    返回分页的用户列表，仅管理员可访问。

    参数:
        pagination: 分页参数
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        Page[User]: 分页的用户列表
    """
    # 计算分页参数
    skip = (pagination.page - 1) * pagination.page_size

    # 获取用户列表和总数
    users, total = await user_service.get_users_with_pagination(
        db, skip=skip, limit=pagination.page_size
    )

    # 构建分页响应
    return Page.create(
        items=users, total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.post("", response_model=UserSchema)
async def create_user(
    user_in: UserCreate,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    创建用户

    创建新用户，仅管理员可访问。

    参数:
        user_in: 用户创建数据
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        User: 创建的用户信息

    异常:
        HTTPException: 用户名或邮箱已存在时抛出
    """
    # 检查用户名是否已存在
    existing_user = await user_service.get_by_username(db, username=user_in.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

    # 检查邮箱是否已存在
    existing_email = await user_service.get_by_email(db, email=user_in.email)
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被注册")

    # 创建用户
    user = await user_service.create(db, obj_in=user_in)
    return user


@router.get("/{user_id}", response_model=UserSchema)
async def read_user(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    获取用户

    返回特定用户的信息，仅管理员可访问。

    参数:
        user_id: 用户ID
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        User: 用户信息

    异常:
        HTTPException: 用户不存在时抛出
    """
    user = await user_service.get(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    更新用户

    更新用户信息，仅管理员可访问。

    参数:
        user_id: 用户ID
        user_in: 用户更新数据
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        User: 更新后的用户信息

    异常:
        HTTPException: 用户不存在或用户名/邮箱已存在时抛出
    """
    # 获取用户
    user = await user_service.get(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 不允许降级最后一个管理员
    if (
        user.role == UserRole.ADMIN
        and user_in.role == UserRole.USER
        and user_id != str(current_user.id)
    ):
        # 检查是否还有其他管理员
        users, _ = await user_service.get_users_with_pagination(db, skip=0, limit=100)
        admin_count = sum(1 for u in users if u.role == UserRole.ADMIN)
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="不能降级唯一的管理员"
            )

    # 检查用户名是否已存在
    if user_in.username and user_in.username != user.username:
        existing_user = await user_service.get_by_username(
            db, username=user_in.username
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在"
            )

    # 检查邮箱是否已存在
    if user_in.email and user_in.email != user.email:
        existing_email = await user_service.get_by_email(db, email=user_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被注册"
            )

    # 更新用户信息
    updated_user = await user_service.update(db, db_obj=user, obj_in=user_in)
    return updated_user


@router.delete("/{user_id}", response_model=Message)
async def delete_user(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Message:
    """
    删除用户

    删除用户，仅管理员可访问。

    参数:
        user_id: 用户ID
        current_user: 当前登录用户
        db: 数据库会话

    返回:
        Message: 操作结果消息

    异常:
        HTTPException: 用户不存在或尝试删除自己时抛出
    """
    # 不能删除自己
    if user_id == str(current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己")

    # 获取用户
    user = await user_service.get(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 不允许删除最后一个管理员
    if user.role == UserRole.ADMIN:
        # 检查是否还有其他管理员
        users, _ = await user_service.get_users_with_pagination(db, skip=0, limit=100)
        admin_count = sum(1 for u in users if u.role == UserRole.ADMIN)
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除唯一的管理员"
            )

    # 删除用户
    await user_service.remove(db, id=user_id)

    return Message(detail="用户已成功删除")
