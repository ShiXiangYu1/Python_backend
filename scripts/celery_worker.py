#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Celery Worker启动脚本

该脚本用于启动Celery Worker，处理异步任务。
支持配置不同的队列、并发数和日志级别。
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
logger = logging.getLogger("celery_worker")


def parse_arguments():
    """
    解析命令行参数
    
    定义并解析命令行参数，包括队列、并发数和日志级别等。
    
    返回:
        argparse.Namespace: 解析后的命令行参数
    """
    parser = argparse.ArgumentParser(description='启动Celery Worker')
    
    parser.add_argument(
        '--queues',
        '-Q',
        default='default',
        help='要监听的队列，逗号分隔的列表，例如: high_priority,default,low_priority'
    )
    
    parser.add_argument(
        '--concurrency',
        '-c',
        type=int,
        default=os.cpu_count(),
        help='Worker进程数，默认使用CPU核心数'
    )
    
    parser.add_argument(
        '--loglevel',
        '-l',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='日志级别'
    )
    
    parser.add_argument(
        '--beat',
        '-B',
        action='store_true',
        help='是否同时启动Celery Beat (用于定时任务)'
    )
    
    parser.add_argument(
        '--pool',
        '-p',
        default='prefork',
        choices=['prefork', 'eventlet', 'gevent', 'solo'],
        help='进程池实现'
    )
    
    return parser.parse_args()


def start_worker(args):
    """
    启动Celery Worker
    
    根据命令行参数配置并启动Celery Worker。
    
    参数:
        args (argparse.Namespace): 命令行参数
    """
    logger.info(f"启动Celery Worker，监听队列: {args.queues}")
    logger.info(f"并发数: {args.concurrency}")
    logger.info(f"日志级别: {args.loglevel}")
    logger.info(f"进程池: {args.pool}")
    if args.beat:
        logger.info("同时启动Celery Beat")
    
    # 组装Celery Worker命令行参数
    worker_args = [
        'worker',
        '--queues', args.queues,
        '--concurrency', str(args.concurrency),
        '--loglevel', args.loglevel,
        '--pool', args.pool,
    ]
    
    # 如果需要同时启动Beat，添加相应参数
    if args.beat:
        worker_args.append('--beat')
    
    # 启动Celery Worker
    celery_app.worker_main(worker_args)


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


if __name__ == "__main__":
    # 设置环境变量
    setup_environment()
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 启动Worker
    start_worker(args) 