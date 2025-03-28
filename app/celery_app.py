#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Celery应用配置模块

配置Celery实例，包括消息代理、结果后端、任务队列和路由策略等。
该模块是连接FastAPI应用和Celery任务系统的桥梁。
"""

import os
from celery import Celery
from kombu import Exchange, Queue

# 加载环境变量
broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# 创建Celery实例
celery_app = Celery(
    "app",
    broker=broker_url,
    backend=result_backend,
    include=[
        "app.tasks.common_tasks",
        "app.tasks.model_tasks",
        "app.tasks.high_priority_tasks",
    ],
)

# 配置Celery
celery_app.conf.update(
    # 时区设置
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务执行设置
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 结果过期时间
    result_expires=3600 * 24 * 7,  # 7天
    
    # 任务跟踪
    task_track_started=True,
    task_ignore_result=False,
    
    # 任务重试
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # 定时任务配置
    beat_schedule={
        "system-health-check-every-hour": {
            "task": "app.tasks.high_priority_tasks.system_health_check",
            "schedule": 3600.0,  # 每小时执行一次
            "args": (["database", "redis", "storage", "api", "worker"],),
            "options": {"queue": "high_priority"},
        },
        "cleanup-old-data-daily": {
            "task": "app.tasks.common_tasks.cleanup_old_data",
            "schedule": 86400.0,  # 每天执行一次
            "args": (30, ["logs", "temp_files", "old_records"]),
            "options": {"queue": "low_priority"},
        },
    },
    
    # 默认的任务队列
    task_default_queue="default",
    
    # 定义交换机
    task_queues=(
        Queue("high_priority", Exchange("high_priority"), routing_key="high_priority.*"),
        Queue("default", Exchange("default"), routing_key="default.*"),
        Queue("low_priority", Exchange("low_priority"), routing_key="low_priority.*"),
    ),
    
    # 任务路由
    task_routes={
        # 高优先级任务
        "app.tasks.high_priority_tasks.*": {"queue": "high_priority", "routing_key": "high_priority.tasks"},
        
        # 默认任务
        "app.tasks.common_tasks.*": {"queue": "default", "routing_key": "default.tasks"},
        
        # 低优先级任务
        "app.tasks.low_priority_tasks.*": {"queue": "low_priority", "routing_key": "low_priority.tasks"},
        
        # 模型相关任务（可根据具体需求设置优先级）
        "app.tasks.model_tasks.deploy_model": {"queue": "high_priority", "routing_key": "high_priority.model"},
        "app.tasks.model_tasks.validate_model": {"queue": "default", "routing_key": "default.model"},
    },
)


# 获取任务路由信息，根据任务名称和优先级设置队列
def get_task_queue(task_name, priority=None):
    """
    根据任务名称和优先级获取队列名称
    
    根据设定的路由规则，将任务分配到合适的队列。如果指定了优先级，
    则会覆盖默认路由规则。
    
    参数:
        task_name: 任务名称
        priority: 任务优先级 (high, normal, low)
        
    返回:
        str: 队列名称
    """
    if priority == "high":
        return "high_priority"
    elif priority == "low":
        return "low_priority"
    
    # 使用任务路由规则
    routes = celery_app.conf.task_routes or {}
    for pattern, route in routes.items():
        if task_name.startswith(pattern.replace(".*", "")):
            return route.get("queue", "default")
    
    return "default"


# 在worker启动时打印配置信息
@celery_app.on_after_configure.connect
def setup_logger(sender, **kwargs):
    """在Celery Worker配置完成后设置日志，打印配置信息"""
    import logging
    logger = logging.getLogger("celery")
    logger.info("Celery worker started with configuration:")
    logger.info(f"Broker URL: {broker_url}")
    logger.info(f"Result Backend: {result_backend}")
    logger.info(f"Task Queues: {[q.name for q in celery_app.conf.task_queues]}")


# 在worker初始化时的操作
@celery_app.signals.worker_init.connect
def worker_init(**kwargs):
    """Worker初始化时的处理函数"""
    import logging
    logger = logging.getLogger("celery")
    logger.info("Worker initialized")


# 在worker关闭时的操作
@celery_app.signals.worker_shutdown.connect
def worker_shutdown(**kwargs):
    """Worker关闭时的处理函数"""
    import logging
    logger = logging.getLogger("celery")
    logger.info("Worker shutting down")


if __name__ == "__main__":
    celery_app.start() 