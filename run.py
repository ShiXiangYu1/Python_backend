#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多进程Uvicorn启动脚本

此脚本用于在生产环境中以多进程模式启动FastAPI应用，
提高并发处理能力和CPU利用率。
"""

import os
import sys
import multiprocessing
import uvicorn
from app.core.config import settings


def get_optimal_workers():
    """
    计算最优的工作进程数量
    
    基于CPU核心数计算最优的工作进程数量，一般为(2 * CPU核心数 + 1)。
    但会限制在最小2个，最大16个的范围内，以避免资源过度占用。
    
    返回:
        int: 最优的工作进程数量
    """
    cores = multiprocessing.cpu_count()
    workers = min(max(int(cores * 2 + 1), 2), 16)
    return workers


def run_multi_process_server():
    """
    以多进程模式运行Uvicorn服务器
    
    启动具有多个工作进程的Uvicorn服务器，提高并发处理能力。
    只在生产环境中使用多进程模式，开发环境仍使用单进程以支持热重载。
    """
    # 确定工作进程数量
    if settings.APP_ENV == "production":
        # 生产环境：使用计算的最优进程数
        workers = get_optimal_workers()
        reload = False
    else:
        # 开发环境：使用单进程以支持热重载
        workers = 1
        reload = settings.APP_DEBUG
    
    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        workers=workers,
        reload=reload,
        log_level=settings.LOG_LEVEL.lower(),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
    
    print(f"服务已启动: http://{settings.APP_HOST}:{settings.APP_PORT}")
    print(f"环境: {settings.APP_ENV}")
    print(f"工作进程数: {workers}")
    print(f"日志级别: {settings.LOG_LEVEL}")


if __name__ == "__main__":
    run_multi_process_server() 