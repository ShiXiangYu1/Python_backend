#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
计时中间件模块

提供请求处理时间监控功能，在HTTP响应头中添加处理时间信息。
帮助开发者和客户端监控API性能。
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint


class TimingMiddleware:
    """
    计时中间件
    
    记录请求处理时间，并在响应头中添加处理时间信息。
    """
    
    async def __call__(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        处理请求
        
        记录请求处理时间，并在响应头中添加处理时间信息。
        
        参数:
            request: HTTP请求
            call_next: 下一个中间件
            
        返回:
            Response: HTTP响应
        """
        start_time = time.time()
        
        # 调用下一个中间件
        response = await call_next(request)
        
        # 计算处理时间
        process_time = (time.time() - start_time) * 1000
        
        # 添加响应头
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        
        return response 