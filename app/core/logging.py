#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志配置模块

该模块负责设置和配置应用程序的日志系统，支持控制台输出和文件记录，
并提供不同日志级别的颜色区分。使用Python标准库的logging模块和第三方库loguru。
"""

import os
import sys
import logging
from pathlib import Path
from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """
    设置应用程序日志系统

    配置日志格式、日志级别、输出位置等。同时集成Python标准库的logging和loguru。
    创建日志目录（如果不存在），并配置日志文件的轮转策略。

    返回:
        None
    """
    # 创建日志目录（如果不存在）
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 配置日志级别
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # 配置标准库logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 配置loguru
    # 移除默认的sink
    logger.remove()

    # 添加控制台输出，带颜色
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # 添加文件输出，按天轮转
    logger.add(
        os.path.join(settings.LOG_DIR, "app_{time:YYYY-MM-DD}.log"),
        level=settings.LOG_LEVEL.upper(),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
    )

    # 为某些过于啰嗦的库调整日志级别
    for module_name in ["uvicorn.access", "sqlalchemy.engine"]:
        logging.getLogger(module_name).setLevel(logging.WARNING)

    # 记录启动信息
    logger.info(f"日志系统初始化完成，日志级别: {settings.LOG_LEVEL}")
    logger.info(f"日志文件存储在: {os.path.abspath(settings.LOG_DIR)}")


def get_logger(name: str) -> logger:
    """
    获取命名的logger实例

    为指定的模块创建一个logger实例，方便追踪日志来源。

    参数:
        name: 模块名称，通常使用__name__

    返回:
        logger: 配置好的logger实例
    """
    return logger.bind(name=name)
