#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
安全模块

提供安全相关的功能，包括密码哈希生成与验证、JWT令牌创建与解码、
访问权限控制等。保障应用的用户认证和授权安全。
"""

from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings


# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2密码流认证
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PREFIX}/auth/login"
)


def create_password_hash(password: str) -> str:
    """
    创建密码哈希
    
    对原始密码进行哈希处理，用于安全存储。
    
    参数:
        password: 原始密码
        
    返回:
        str: 密码哈希值
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    验证原始密码是否与存储的哈希匹配。
    
    参数:
        plain_password: 原始密码
        hashed_password: 存储的密码哈希
        
    返回:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌
    
    生成包含用户身份和过期时间的JWT令牌。
    
    参数:
        subject: 令牌主体，通常是用户ID
        expires_delta: 令牌有效期
        
    返回:
        str: 编码后的JWT令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    验证令牌
    
    解码并验证JWT令牌的有效性。
    
    参数:
        token: JWT令牌
        
    返回:
        dict: 解码后的令牌载荷
        
    异常:
        HTTPException: 当令牌无效或过期时
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        ) 