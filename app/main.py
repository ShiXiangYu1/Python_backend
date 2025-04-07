#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FastAPI应用主入口

此模块包含FastAPI应用的实例化、中间件配置、路由注册和事件处理逻辑。
作为应用的主入口点，它汇集了所有必要的组件形成一个完整的Web服务。
"""

import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.metrics import setup_metrics
from app.api.routes import api_router
from app.core.logging import setup_logging
from app.db.events import connect_to_db, close_db_connection
from app.db.session import create_db_and_tables
from app.middlewares.security import add_security_middleware


def create_application() -> FastAPI:
    """
    创建并配置FastAPI应用实例

    此函数负责初始化FastAPI应用，配置中间件，注册路由，
    并设置应用启动和关闭事件的处理函数。

    返回:
        FastAPI: 配置好的FastAPI应用实例
    """
    # 设置应用描述和版本
    description = f"""
    {settings.APP_NAME} API 
    
    ## 特性
    
    * **用户管理** - 注册、登录、权限控制
    * **模型管理** - 模型上传、版本控制、元数据管理
    * **模型部署** - API部署、监控、扩展
    * **任务队列** - 异步任务处理
    """

    # 创建FastAPI应用实例
    app = FastAPI(
        title=settings.APP_NAME,
        description=description,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        debug=settings.APP_DEBUG,
    )

    # 配置指标收集
    setup_metrics(app, settings.APP_NAME, "0.1.0")

    # 配置安全中间件（包含CORS、安全头部和CSRF保护）
    add_security_middleware(app, settings.SECRET_KEY)

    # 挂载静态文件目录
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    # 注册路由
    app.include_router(api_router, prefix=settings.API_PREFIX)

    # Web前端路由处理
    from app.web import web_router

    app.include_router(web_router)

    # 注册事件处理器
    @app.on_event("startup")
    async def startup_event():
        """应用启动时执行的事件处理函数"""
        setup_logging()
        logging.info("Starting up application")
        await connect_to_db(app)
        await create_db_and_tables()

        # 初始化缓存系统
        try:
            from app.utils.dependencies import get_redis_client
            from app.utils.cache import initialize_cache

            redis_client = get_redis_client()
            initialize_cache(redis_client)
            logging.info("缓存系统初始化完成")
        except Exception as e:
            logging.error(f"缓存系统初始化失败: {str(e)}")

        # 初始化任务系统
        init_task_system()

    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时执行的事件处理函数"""
        logging.info("Shutting down application")
        await close_db_connection(app)
        shutdown_task_system()

    return app


def init_task_system():
    """
    初始化任务系统

    在应用启动时执行任务系统的初始化操作，包括：
    1. 确保Celery应用已正确配置
    2. 验证Redis连接
    3. 创建必要的任务队列
    4. 初始化任务监控

    该函数在应用启动事件处理程序中被调用。
    """
    from app.celery_app import celery_app
    from app.core.celery import init_celery_logging

    logging.info("初始化任务系统...")

    # 验证Celery应用配置
    try:
        broker_url = celery_app.conf.broker_url
        logging.info(f"Celery broker URL: {broker_url}")

        # 验证Redis连接
        from redis import Redis

        redis_client = Redis.from_url(
            broker_url, socket_connect_timeout=5, socket_timeout=5
        )
        if redis_client.ping():
            logging.info("Redis连接正常")
        else:
            logging.warning("无法连接到Redis")
        redis_client.close()

        # 初始化Celery日志
        init_celery_logging()

        # 检查队列配置
        queues = [q.name for q in celery_app.conf.task_queues or []]
        logging.info(f"已配置任务队列: {', '.join(queues) if queues else '默认队列'}")

        # 检查定时任务配置
        beat_schedule = celery_app.conf.beat_schedule or {}
        logging.info(f"已配置{len(beat_schedule)}个定时任务")

        logging.info("任务系统初始化完成")
    except Exception as e:
        logging.error(f"任务系统初始化失败: {str(e)}")
        # 在开发环境下抛出异常，生产环境下继续运行
        if settings.APP_ENV == "development":
            raise

    # 注册任务系统信号处理程序
    register_task_signals()


def register_task_signals():
    """
    注册任务系统信号处理程序

    配置Celery任务的信号处理程序，用于跟踪任务的状态变化和执行情况。
    这些处理程序将在任务的不同生命周期阶段被调用。
    """
    from celery.signals import (
        task_prerun,
        task_postrun,
        task_failure,
        task_success,
        worker_ready,
    )

    @worker_ready.connect
    def on_worker_ready(**kwargs):
        """当Worker准备就绪时调用"""
        logging.info("Celery Worker已就绪")

    @task_prerun.connect
    def on_task_prerun(task_id=None, task=None, **kwargs):
        """任务开始执行前调用"""
        logging.debug(f"任务开始执行: {task.name}[{task_id}]")

    @task_success.connect
    def on_task_success(sender=None, result=None, **kwargs):
        """任务成功完成时调用"""
        logging.debug(f"任务执行成功: {sender.name}, 结果: {result}")

    @task_failure.connect
    def on_task_failure(sender=None, exception=None, **kwargs):
        """任务执行失败时调用"""
        logging.error(f"任务执行失败: {sender.name}, 错误: {exception}")

    @task_postrun.connect
    def on_task_postrun(task_id=None, task=None, state=None, **kwargs):
        """任务执行完成后调用"""
        logging.debug(f"任务执行完成: {task.name}[{task_id}], 状态: {state}")


def shutdown_task_system():
    """
    停止任务系统

    在应用关闭时执行任务系统的清理操作，包括：
    1. 关闭Celery连接
    2. 取消正在执行的任务
    3. 释放相关资源

    该函数在应用关闭事件处理程序中被调用。
    """
    logging.info("关闭任务系统...")

    # 在这里执行任务系统的清理操作
    # 例如关闭连接、取消任务等

    logging.info("任务系统已关闭")


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
    )
