#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
指标收集模块

提供用于收集应用程序指标的工具，支持Prometheus格式的指标导出。
主要用于监控应用程序性能、资源使用情况和业务数据。
"""

import time
from typing import Callable, Dict, Any

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    Counter, Histogram, Gauge, 
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
    multiprocess, Info
)
from starlette.middleware.base import BaseHTTPMiddleware


# 创建指标注册表
metrics_registry = CollectorRegistry()

# 应用信息指标
app_info = Info(
    "app_info", "Application information", 
    registry=metrics_registry
)

# 请求计数器
http_requests_total = Counter(
    "http_requests_total", 
    "Total count of HTTP requests", 
    ["method", "endpoint", "status_code"],
    registry=metrics_registry
)

# 请求延迟直方图
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", 
    "HTTP request duration in seconds", 
    ["method", "endpoint"],
    registry=metrics_registry
)

# API请求计数器
api_requests_total = Counter(
    "api_requests_total", 
    "Total count of API requests", 
    ["endpoint", "method", "user_id", "status_code"],
    registry=metrics_registry
)

# 模型操作计数器
model_operations_total = Counter(
    "model_operations_total", 
    "Total count of model operations", 
    ["operation", "model_id", "user_id"],
    registry=metrics_registry
)

# 模型部署时间直方图
model_deployment_duration_seconds = Histogram(
    "model_deployment_duration_seconds", 
    "Model deployment duration in seconds", 
    ["model_id"],
    registry=metrics_registry
)

# 活跃用户数量
active_users = Gauge(
    "active_users", 
    "Number of active users in the last 30 minutes",
    registry=metrics_registry
)

# 数据库连接池指标
db_connections_active = Gauge(
    "db_connections_active", 
    "Number of active database connections",
    registry=metrics_registry
)

# API密钥使用计数器
api_key_usage_total = Counter(
    "api_key_usage_total", 
    "Total usage count of API keys", 
    ["api_key_id", "endpoint"],
    registry=metrics_registry
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Prometheus指标收集中间件
    
    记录HTTP请求的数量、延迟和状态码等信息，将这些信息导出为Prometheus指标。
    """
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        处理请求
        
        记录请求的开始时间，执行请求处理，然后记录处理结果和持续时间。
        
        参数:
            request: 传入的HTTP请求
            call_next: 下一个处理函数
            
        返回:
            Response: HTTP响应
        """
        start_time = time.time()
        method = request.method
        status_code = 500  # 默认状态码
        
        # 处理请求
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            status_code = 500
            raise e
        finally:
            # 计算请求处理时间
            duration = time.time() - start_time
            
            # 尝试获取路由路径，如果不可用则使用原始路径
            endpoint = request.scope.get("path", request.url.path)
            
            # 记录请求数量
            http_requests_total.labels(
                method=method, 
                endpoint=endpoint, 
                status_code=str(status_code)
            ).inc()
            
            # 记录请求持续时间
            http_request_duration_seconds.labels(
                method=method, 
                endpoint=endpoint
            ).observe(duration)


def setup_metrics(app: FastAPI, app_name: str, app_version: str) -> None:
    """
    设置应用程序指标
    
    初始化应用程序指标并配置中间件。
    
    参数:
        app: FastAPI应用实例
        app_name: 应用程序名称
        app_version: 应用程序版本
    """
    # 设置应用程序信息
    app_info.info({
        "name": app_name,
        "version": app_version,
        "start_time": str(time.time())
    })
    
    # 添加Prometheus中间件
    app.add_middleware(PrometheusMiddleware)
    
    # 添加指标导出端点
    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        """
        导出Prometheus指标
        
        返回当前收集的所有指标，格式为Prometheus文本格式。
        
        返回:
            Response: 包含Prometheus指标的响应
        """
        return Response(
            content=generate_latest(metrics_registry),
            media_type=CONTENT_TYPE_LATEST
        )


def record_model_operation(operation: str, model_id: str, user_id: str) -> None:
    """
    记录模型操作
    
    记录对模型的操作，如创建、更新、删除和部署。
    
    参数:
        operation: 操作类型，如create、update、delete、deploy
        model_id: 模型ID
        user_id: 用户ID
    """
    model_operations_total.labels(
        operation=operation,
        model_id=model_id,
        user_id=user_id
    ).inc()


def record_model_deployment_time(model_id: str, duration: float) -> None:
    """
    记录模型部署时间
    
    记录模型从开始部署到部署完成的时间。
    
    参数:
        model_id: 模型ID
        duration: 部署持续时间（秒）
    """
    model_deployment_duration_seconds.labels(
        model_id=model_id
    ).observe(duration)


def record_api_key_usage(api_key_id: str, endpoint: str) -> None:
    """
    记录API密钥使用
    
    记录API密钥的使用情况，包括使用次数和访问的端点。
    
    参数:
        api_key_id: API密钥ID
        endpoint: 访问的API端点
    """
    api_key_usage_total.labels(
        api_key_id=api_key_id,
        endpoint=endpoint
    ).inc()


def set_db_connections(active_connections: int) -> None:
    """
    设置数据库连接数
    
    更新当前活跃的数据库连接数。
    
    参数:
        active_connections: 活跃连接数
    """
    db_connections_active.set(active_connections)


def set_active_users_count(count: int) -> None:
    """
    设置活跃用户数
    
    更新当前活跃的用户数量。
    
    参数:
        count: 活跃用户数
    """
    active_users.set(count) 