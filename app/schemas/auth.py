#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
认证Schema模块

定义用户认证相关API的请求和响应数据模型，如登录请求和令牌响应。
用于验证登录请求的格式和生成标准的认证响应。
"""

from typing import Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    """
    令牌响应Schema
    
    用于返回认证成功后的访问令牌和令牌类型。
    """
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")


class TokenPayload(BaseModel):
    """
    令牌载荷Schema
    
    定义JWT令牌中的载荷数据结构。
    """
    sub: Optional[str] = Field(None, description="主题（通常是用户ID）")
    exp: Optional[int] = Field(None, description="过期时间（Unix时间戳）")


class Login(BaseModel):
    """
    登录请求Schema
    
    用于验证用户登录请求的格式。
    """
    username: str = Field(..., description="用户名或电子邮箱")
    password: str = Field(..., description="密码")


class PasswordReset(BaseModel):
    """
    密码重置请求Schema
    
    用于验证密码重置请求的格式。
    """
    email: str = Field(..., description="电子邮箱")


class PasswordChange(BaseModel):
    """
    密码修改请求Schema
    
    用于验证密码修改请求的格式。
    """
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, description="新密码")
    confirm_password: str = Field(..., description="确认新密码") 