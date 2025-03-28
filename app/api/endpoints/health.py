#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
健康检查API端点模块

提供用于监控应用健康状态的端点，包括系统状态、数据库连接状态等。
主要用于容器化环境中的健康检查和监控系统。
"""

import time
from typing import Dict, Any
from typing_extensions import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: Annotated[AsyncSession, Depends(get_db)]) -> Dict[str, Any]:
    """
    健康检查端点
    
    检查应用的健康状态，包括数据库连接和系统版本。
    主要用于容器化环境中的健康检查。
    
    参数:
        db: 数据库会话
        
    返回:
        Dict[str, Any]: 健康状态信息
    """
    # 系统状态
    status_info = {
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": settings.PROJECT_VERSION,
        "environment": settings.APP_ENV,
    }
    
    # 检查数据库连接
    try:
        # 简单的数据库查询以验证连接
        await db.execute(text("SELECT 1"))
        status_info["database"] = "connected"
    except Exception as e:
        status_info["status"] = "unhealthy"
        status_info["database"] = "disconnected"
        status_info["database_error"] = str(e)
    
    return status_info 