#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Celery Beat启动脚本

该脚本用于启动Celery Beat服务，处理定时任务的调度。
支持配置调度器存储位置、日志级别等参数。
"""

import os
import argparse
import logging
from pathlib import Path

from app.celery_app import celery_app


# 设置日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("celery_beat")


def parse_arguments():
    """
    解析命令行参数
    
    定义并解析命令行参数，包括调度器、日志级别等。
    
    返回:
        argparse.Namespace: 解析后的命令行参数
    """
    parser = argparse.ArgumentParser(description='启动Celery Beat服务')
    
    parser.add_argument(
        '--loglevel',
        '-l',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='日志级别'
    )
    
    parser.add_argument(
        '--scheduler',
        '-s',
        default='celery.beat.PersistentScheduler',
        help='调度器类，默认使用持久化调度器'
    )
    
    parser.add_argument(
        '--schedule',
        '-S',
        default='celerybeat-schedule',
        help='调度器数据库文件路径'
    )
    
    parser.add_argument(
        '--max-interval',
        '-m',
        type=int,
        default=300,  # 5分钟
        help='调度器的最大间隔时间（秒）'
    )
    
    return parser.parse_args()


def start_beat(args):
    """
    启动Celery Beat
    
    根据命令行参数配置并启动Celery Beat服务。
    
    参数:
        args (argparse.Namespace): 命令行参数
    """
    logger.info("启动Celery Beat服务")
    logger.info(f"日志级别: {args.loglevel}")
    logger.info(f"调度器: {args.scheduler}")
    logger.info(f"调度数据库: {args.schedule}")
    logger.info(f"最大间隔: {args.max_interval}秒")
    
    # 组装Celery Beat命令行参数
    beat_args = [
        'beat',
        '--loglevel', args.loglevel,
        '--scheduler', args.scheduler,
        '--schedule', args.schedule,
        '--max-interval', str(args.max_interval),
    ]
    
    # 启动Celery Beat
    celery_app.start(beat_args)


def setup_environment():
    """
    设置环境变量
    
    确保必要的环境变量已设置，如果不存在则设置默认值。
    """
    # 设置Python路径，确保可以导入应用模块
    project_root = str(Path(__file__).parent.parent.absolute())
    if project_root not in os.environ.get('PYTHONPATH', ''):
        if 'PYTHONPATH' in os.environ:
            os.environ['PYTHONPATH'] = f"{os.environ['PYTHONPATH']}:{project_root}"
        else:
            os.environ['PYTHONPATH'] = project_root
    
    # 设置默认的Celery Broker URL
    if 'CELERY_BROKER_URL' not in os.environ:
        default_broker = "redis://localhost:6379/0"
        logger.warning(f"环境变量CELERY_BROKER_URL未设置，使用默认值: {default_broker}")
        os.environ['CELERY_BROKER_URL'] = default_broker
    
    # 设置默认的Celery Result Backend
    if 'CELERY_RESULT_BACKEND' not in os.environ:
        default_backend = "redis://localhost:6379/0"
        logger.warning(f"环境变量CELERY_RESULT_BACKEND未设置，使用默认值: {default_backend}")
        os.environ['CELERY_RESULT_BACKEND'] = default_backend
    
    # 在Windows环境下设置事件循环策略，解决asyncio的问题
    if os.name == 'nt':
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def create_schedule_dir(schedule_path):
    """
    创建调度器数据目录
    
    确保调度器数据文件的目录存在，如果不存在则创建。
    
    参数:
        schedule_path (str): 调度器数据文件路径
    """
    # 获取调度器数据文件所在目录
    schedule_dir = os.path.dirname(os.path.abspath(schedule_path))
    
    # 如果目录不存在，创建它
    if not os.path.exists(schedule_dir) and schedule_dir:
        logger.info(f"创建调度器数据目录: {schedule_dir}")
        os.makedirs(schedule_dir, exist_ok=True)


if __name__ == "__main__":
    # 设置环境变量
    setup_environment()
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 确保调度器数据目录存在
    create_schedule_dir(args.schedule)
    
    # 启动Beat
    start_beat(args) 