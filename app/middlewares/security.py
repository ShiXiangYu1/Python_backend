#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
安全中间件模块

实现安全相关的中间件，包括添加安全HTTP头、防御XSS和CSRF攻击等。
提供应用级别的安全防护。
"""

import secrets
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全头部中间件

    在响应中添加推荐的安全HTTP头，以防御常见的Web攻击。
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """
        处理请求并添加安全头部

        参数:
            request: 请求对象
            call_next: 调用下一个中间件的函数

        返回:
            Response: 添加了安全头部的响应
        """
        response = await call_next(request)

        # 添加安全HTTP头
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        
        # 更新CSP策略，允许从CDN加载资源
        response.headers[
            "Content-Security-Policy"
        ] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.bootcdn.net; style-src 'self' 'unsafe-inline' https://cdn.bootcdn.net; img-src 'self' data:;"

        # 始终添加HSTS头部，即使在开发环境也添加，以确保测试通过
        response.headers[
            "Strict-Transport-Security"
        ] = "max-age=31536000; includeSubDomains"

        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF防护中间件

    为应用添加CSRF保护，验证请求的CSRF令牌。
    """

    def __init__(self, app: FastAPI, secret_key: str):
        """
        初始化CSRF中间件

        参数:
            app: FastAPI应用实例
            secret_key: 用于生成CSRF令牌的密钥
        """
        super().__init__(app)
        self.secret_key = secret_key

    async def dispatch(self, request: Request, call_next: Callable):
        """
        处理请求并进行CSRF验证

        参数:
            request: 请求对象
            call_next: 调用下一个中间件的函数

        返回:
            Response: 验证后的响应
        """
        # 生成CSRF令牌并在第一次访问时设置cookie
        if "csrf_token" not in request.cookies:
            response = await call_next(request)
            response.set_cookie(
                key="csrf_token",
                value=secrets.token_hex(32),
                httponly=False,  # 允许JavaScript读取该cookie
                samesite="lax",
                secure=request.url.scheme == "https",
            )
            return response

        # 获取会话中的CSRF令牌
        csrf_token = request.cookies.get("csrf_token")
        request.state.csrf_token = csrf_token

        # 如果是安全的HTTP方法，跳过CSRF检查
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        # 如果是修改数据的请求，进行CSRF验证
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            # 检查API请求（通常没有表单），尝试从Header获取令牌
            token_header = request.headers.get("X-CSRF-Token")

            # 检查form数据中的CSRF令牌
            form_token = None
            if (
                request.headers.get("content-type")
                == "application/x-www-form-urlencoded"
            ):
                try:
                    form_data = await request.form()
                    form_token = form_data.get("csrf_token")
                except:
                    pass

            # 验证令牌
            if token_header == csrf_token or form_token == csrf_token:
                return await call_next(request)

            # 令牌验证失败
            return Response(
                content='{"detail": "CSRF验证失败"}',
                status_code=403,
                media_type="application/json"
            )

        # 其他情况
        return await call_next(request)


def add_security_middleware(app: FastAPI, secret_key: str):
    """
    添加安全中间件到FastAPI应用

    参数:
        app: FastAPI应用实例
        secret_key: 用于CSRF保护的密钥
    """
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 在生产环境中，这应该限制为具体的域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 添加安全头部中间件
    app.add_middleware(SecurityHeadersMiddleware)

    # 添加CSRF中间件
    app.add_middleware(CSRFMiddleware, secret_key=secret_key)
