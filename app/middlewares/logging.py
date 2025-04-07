#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志中间件模块

提供HTTP请求日志记录功能，记录每个请求的方法、路径、状态码和处理时间。
帮助开发者追踪API调用并进行问题排查。
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint


logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    请求日志中间件

    记录所有HTTP请求的详细信息，包括请求方法、路径、状态码和处理时间。
    """

    async def __call__(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        处理请求

        记录请求信息，调用下一个中间件，然后记录响应信息。

        参数:
            request: HTTP请求
            call_next: 下一个中间件

        返回:
            Response: HTTP响应
        """
        start_time = time.time()

        # 记录请求信息
        logger.info(f"Request: {request.method} {request.url.path}")

        # 调用下一个中间件
        response = await call_next(request)

        # 计算处理时间
        process_time = (time.time() - start_time) * 1000

        # 记录响应信息
        logger.info(
            f"Response: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Process Time: {process_time:.2f}ms"
        )

        return response
