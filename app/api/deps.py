#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API依赖项模块

提供路由处理器所需的依赖项函数，如当前用户获取、权限检查等。
使用FastAPI的依赖注入系统实现，方便在路由处理器中复用。
"""

from typing import Optional
from typing_extensions import Annotated
import time
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Security, status, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_token
from app.core.metrics import record_api_key_usage, set_active_users_count
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.api_key import APIKey
from app.schemas.auth import TokenPayload
from app.services.user import user_service
from app.services.api_key import api_key_service


# OAuth2密码授权表单，用于JWT认证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")

# API密钥请求头，用于API密钥认证
api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)

# 活跃用户缓存
_active_users = {}


# 定期清理过期的活跃用户
def cleanup_active_users():
    """清理30分钟前的活跃用户"""
    now = datetime.now()
    cutoff = now - timedelta(minutes=30)

    # 移除超过30分钟未活动的用户
    expired_users = [
        user_id
        for user_id, last_active in _active_users.items()
        if last_active < cutoff
    ]
    for user_id in expired_users:
        _active_users.pop(user_id, None)

    # 更新活跃用户计数
    set_active_users_count(len(_active_users))


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    获取当前用户

    从JWT令牌解析用户信息，并从数据库获取完整的用户对象。
    用于需要用户登录的API端点。

    参数:
        token: JWT令牌
        db: 数据库会话

    返回:
        User: 当前用户对象

    异常:
        HTTPException: 认证失败时抛出
    """
    try:
        # 解码令牌
        payload = verify_token(token)
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = token_data.sub
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户
    user = await user_service.get(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已停用",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 更新活跃用户记录
    _active_users[str(user.id)] = datetime.now()
    cleanup_active_users()

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    获取当前活跃用户

    确保当前用户处于活跃状态。

    参数:
        current_user: 当前用户对象

    返回:
        User: 当前活跃用户对象

    异常:
        HTTPException: 用户不活跃时抛出
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已停用",
        )
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    获取当前管理员用户

    确保当前用户具有管理员权限。

    参数:
        current_user: 当前用户对象

    返回:
        User: 当前管理员用户对象

    异常:
        HTTPException: 用户不是管理员时抛出
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足",
        )
    return current_user


async def get_api_key(
    api_key: Annotated[Optional[str], Security(api_key_header)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
) -> Optional[APIKey]:
    """
    获取API密钥

    从请求头中获取API密钥，并验证其有效性。

    参数:
        api_key: API密钥值
        db: 数据库会话
        request: 当前请求

    返回:
        Optional[APIKey]: API密钥对象，如果未提供或无效则为None
    """
    if not api_key:
        return None

    api_key_obj = await api_key_service.verify_key(db, key=api_key)

    if api_key_obj:
        # 记录API密钥使用情况
        record_api_key_usage(api_key_obj.id, request.url.path)

        # 更新API密钥使用统计
        api_key_obj.last_used_at = datetime.now()
        api_key_obj.usage_count += 1
        await db.commit()

    return api_key_obj


async def get_current_user_from_api_key(
    api_key: Annotated[Optional[APIKey], Depends(get_api_key)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Optional[User]:
    """
    从API密钥获取当前用户

    根据API密钥获取关联的用户。

    参数:
        api_key: API密钥对象
        db: 数据库会话

    返回:
        Optional[User]: 用户对象，如果API密钥无效则为None
    """
    if not api_key:
        return None

    user = await user_service.get(db, api_key.user_id)
    if not user or not user.is_active:
        return None

    # 更新活跃用户记录
    _active_users[str(user.id)] = datetime.now()
    cleanup_active_users()

    return user


async def get_current_user_from_token_or_api_key(
    token_user: Annotated[Optional[User], Depends(get_current_user)],
    api_key_user: Annotated[Optional[User], Depends(get_current_user_from_api_key)],
) -> User:
    """
    从令牌或API密钥获取当前用户

    尝试从JWT令牌或API密钥获取当前用户，支持两种认证方式。

    参数:
        token_user: 从JWT令牌获取的用户
        api_key_user: 从API密钥获取的用户

    返回:
        User: 当前用户对象

    异常:
        HTTPException: 认证失败时抛出
    """
    if token_user:
        return token_user
    if api_key_user:
        return api_key_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
