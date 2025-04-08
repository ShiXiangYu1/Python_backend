#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
认证API模块

处理用户认证相关的API端点，如登录、注册、密码重置等。
提供安全的用户身份验证和访问控制。
"""

from datetime import timedelta
from typing_extensions import Annotated
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import Token, Login, PasswordChange, PasswordReset
from app.schemas.common import Message
from app.schemas.user import User, UserCreate
from app.services.user import user_service


# 创建路由器
router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    用户登录

    验证用户凭据并返回访问令牌。

    参数:
        form_data: 表单数据，包含用户名和密码
        db: 数据库会话

    返回:
        Token: 包含访问令牌和令牌类型的响应

    异常:
        HTTPException: 认证失败时抛出
    """
    # 认证用户
    user = await user_service.authenticate(
        db, username_or_email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已停用",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/login/json", response_model=Token)
async def login_json(
    login_data: Login, db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    """
    JSON格式用户登录

    提供JSON格式的登录接口，与表单登录功能相同。

    参数:
        login_data: JSON格式的登录数据
        db: 数据库会话

    返回:
        Token: 包含访问令牌和令牌类型的响应

    异常:
        HTTPException: 认证失败时抛出
    """
    # 认证用户
    user = await user_service.authenticate(
        db, username_or_email=login_data.username, password=login_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已停用",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=User)
async def register(
    user_in: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    用户注册

    创建新用户并返回用户信息。

    参数:
        user_in: 用户创建数据
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


@router.post("/password-reset", response_model=Message)
async def password_reset(
    reset_data: PasswordReset, db: Annotated[AsyncSession, Depends(get_db)]
) -> Message:
    """
    密码重置

    发送密码重置链接到用户邮箱。

    参数:
        reset_data: 密码重置数据
        db: 数据库会话

    返回:
        Message: 操作结果消息

    异常:
        HTTPException: 邮箱不存在时抛出
    """
    # 检查邮箱是否存在
    user = await user_service.get_by_email(db, email=reset_data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邮箱不存在")

    # TODO: 实现发送密码重置邮件的逻辑
    # 此处应生成重置令牌，并发送包含重置链接的邮件

    return Message(detail="密码重置邮件已发送，请检查您的邮箱")


@router.post("/password-change", response_model=Message)
async def password_change(
    change_data: PasswordChange,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Message:
    """
    密码修改

    修改当前用户的密码。

    参数:
        change_data: 密码修改数据
        db: 数据库会话
        current_user: 当前登录用户

    返回:
        Message: 操作结果消息

    异常:
        HTTPException: 当前密码错误或新密码不匹配时抛出
    """
    # 检查当前密码是否正确
    authenticated_user = await user_service.authenticate(
        db,
        username_or_email=current_user.username,
        password=change_data.current_password,
    )
    if not authenticated_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码错误")

    # 检查新密码和确认密码是否匹配
    if change_data.new_password != change_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="新密码和确认密码不匹配"
        )

    # 更新密码
    await user_service.update(
        db, db_obj=current_user, obj_in={"password": change_data.new_password}
    )

    return Message(detail="密码已成功修改")


@router.get("/csrf-token", response_model=Dict[str, str])
async def get_csrf_token(request: Request) -> Dict[str, str]:
    """
    获取CSRF令牌
    
    此端点用于前端获取CSRF令牌，并直接在响应中返回令牌值。
    同时，CSRFMiddleware也会将令牌设置在cookie中。
    
    返回:
        Dict[str, str]: 包含CSRF令牌的字典
    """
    # 从请求状态中获取CSRF令牌
    csrf_token = getattr(request.state, "csrf_token", "")
    
    # 如果令牌不存在，说明中间件可能尚未设置令牌
    if not csrf_token:
        # 返回消息，提示前端刷新页面
        return {"detail": "CSRF令牌未设置，请刷新页面重试", "token": ""}
    
    # 返回包含令牌的响应
    return {"detail": "CSRF令牌获取成功", "token": csrf_token}
