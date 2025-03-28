#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API路由主模块

该模块作为API路由的主入口点，集成所有功能模块的路由。
负责将各个子路由注册到主路由器，便于在应用主模块中统一挂载。
"""

from fastapi import APIRouter

from app.api.endpoints import auth, users, api_keys, models, health, tasks


# 创建主路由器
api_router = APIRouter()

# 注册各个子路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["API密钥"])
api_router.include_router(models.router, prefix="/models", tags=["模型"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务"])
api_router.include_router(health.router, prefix="", tags=["系统"]) 