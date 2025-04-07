#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Worker池管理模块

提供Celery Worker池的管理功能，包括动态扩缩容、状态监控和负载均衡。
"""

import os
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Tuple

from app.core.celery import celery_app

logger = logging.getLogger(__name__)


class WorkerPool:
    """
    Worker池管理类

    管理Celery Worker池，提供状态监控、动态扩缩和负载均衡功能。
    使用单例模式确保系统中只有一个Worker池管理器。
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式实现"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WorkerPool, cls).__new__(cls)
                cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化Worker池管理器"""
        # 上次检查时间
        self._last_check_time = 0
        # 检查间隔（秒）
        self._check_interval = int(os.getenv("WORKER_CHECK_INTERVAL", "60"))
        # 缓存的Worker状态
        self._worker_stats = {}
        # 队列状态
        self._queue_stats = {}
        # 监控线程
        self._monitor_thread = None
        # 是否运行监控
        self._running = False

        logger.info("Worker池管理器已初始化")

    def start_monitoring(self):
        """
        启动Worker池监控

        在后台线程中定期监控Worker状态和队列负载，并根据需要调整Worker池。
        """
        if self._running:
            logger.warning("Worker池监控已经在运行")
            return

        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True, name="worker-pool-monitor"
        )
        self._monitor_thread.start()
        logger.info("Worker池监控已启动")

    def stop_monitoring(self):
        """
        停止Worker池监控

        停止监控线程。
        """
        if not self._running:
            logger.warning("Worker池监控未在运行")
            return

        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Worker池监控已停止")

    def _monitoring_loop(self):
        """监控循环，定期检查Worker状态和队列负载"""
        while self._running:
            try:
                # 检查Worker状态
                self.check_worker_status()

                # 根据队列负载调整Worker池
                self.balance_workers()

                # 记录当前状态
                self._log_current_status()
            except Exception as e:
                logger.error(f"Worker池监控出错: {e}")

            # 等待下一次检查
            time.sleep(self._check_interval)

    def check_worker_status(self) -> Dict[str, Dict[str, Any]]:
        """
        检查Worker状态

        获取所有Worker的状态信息，包括活跃任务数、处理的任务数等。

        返回:
            Dict[str, Dict[str, Any]]: Worker名称到状态信息的映射
        """
        try:
            # 获取Worker状态
            inspection = celery_app.control.inspect()

            # 活跃Worker
            active_workers = inspection.active() or {}

            # Worker统计信息
            stats = inspection.stats() or {}

            # 更新Worker状态
            self._worker_stats = {}
            for worker_name, worker_stats in stats.items():
                active_tasks = len(active_workers.get(worker_name, []))

                self._worker_stats[worker_name] = {
                    "active_tasks": active_tasks,
                    "processed": worker_stats.get("total", {}).get("processed", 0),
                    "uptime": worker_stats.get("uptime", 0),
                    "pid": worker_stats.get("pid"),
                    "concurrency": worker_stats.get("pool", {}).get(
                        "max-concurrency", 1
                    ),
                    "load": active_tasks
                    / max(worker_stats.get("pool", {}).get("max-concurrency", 1), 1),
                    "last_update": time.time(),
                }

            # 更新队列状态
            self._update_queue_stats()

            self._last_check_time = time.time()
            return self._worker_stats
        except Exception as e:
            logger.error(f"检查Worker状态失败: {e}")
            return {}

    def _update_queue_stats(self):
        """更新队列状态"""
        try:
            # 获取队列长度
            from app.core.celery import celery_helper

            queue_lengths = celery_helper.get_task_queue_lengths()

            # 使用队列长度和平均处理时间计算负载
            for queue, length in queue_lengths.items():
                if queue not in self._queue_stats:
                    self._queue_stats[queue] = {
                        "length": 0,
                        "avg_processing_time": 10.0,  # 默认假设10秒
                        "last_update": 0,
                    }

                # 更新队列长度
                self._queue_stats[queue]["length"] = length
                self._queue_stats[queue]["last_update"] = time.time()
        except Exception as e:
            logger.error(f"更新队列状态失败: {e}")

    def balance_workers(self):
        """
        平衡Worker负载

        根据队列长度和Worker负载，动态调整Worker池大小。
        """
        # 这里仅记录建议，实际扩缩容需要根据部署环境实现
        for queue, stats in self._queue_stats.items():
            # 检查队列长度
            length = stats["length"]

            # 计算队列中任务数与Worker数的比例
            workers_for_queue = sum(
                1
                for _, w_stats in self._worker_stats.items()
                if w_stats.get("active_tasks", 0) < w_stats.get("concurrency", 1)
            )

            # 如果队列长度大于空闲Worker数的2倍，建议扩容
            if length > workers_for_queue * 2 and length > 10:
                logger.info(f"队列 {queue} 负载过高 (长度: {length})，建议扩容Worker")

            # 如果队列长度为0且存在多个Worker，建议缩容
            elif length == 0 and workers_for_queue > 1:
                logger.info(f"队列 {queue} 负载过低，建议缩容Worker")

    def _log_current_status(self):
        """记录当前Worker池状态"""
        if not self._worker_stats:
            logger.warning("没有活跃的Worker")
            return

        logger.info(f"当前Worker池状态: {len(self._worker_stats)}个Worker活跃")
        for worker_name, stats in self._worker_stats.items():
            logger.info(
                f"  {worker_name}: "
                f"活跃任务 {stats.get('active_tasks', 0)}/{stats.get('concurrency', 1)}, "
                f"负载 {stats.get('load', 0):.2f}"
            )

        logger.info(f"当前队列状态:")
        for queue, stats in self._queue_stats.items():
            logger.info(f"  {queue}: 长度 {stats.get('length', 0)}")

    def get_worker_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        获取Worker统计信息

        返回Worker的统计信息，包括活跃任务数、负载等。

        返回:
            Dict[str, Dict[str, Any]]: Worker名称到统计信息的映射
        """
        # 如果统计信息过期，重新获取
        if time.time() - self._last_check_time > self._check_interval:
            self.check_worker_status()

        return self._worker_stats

    def get_queue_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        获取队列统计信息

        返回队列的统计信息，包括长度、平均处理时间等。

        返回:
            Dict[str, Dict[str, Any]]: 队列名称到统计信息的映射
        """
        # 如果统计信息过期，重新获取
        if time.time() - self._last_check_time > self._check_interval:
            self.check_worker_status()

        return self._queue_stats

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """
        获取活跃任务列表

        返回所有Worker上正在执行的任务列表。

        返回:
            List[Dict[str, Any]]: 活跃任务列表
        """
        try:
            # 获取活跃任务
            inspection = celery_app.control.inspect()
            active = inspection.active() or {}

            # 处理活跃任务
            active_tasks = []
            for worker_name, tasks in active.items():
                for task in tasks:
                    active_tasks.append(
                        {
                            "id": task["id"],
                            "name": task["name"],
                            "args": task["args"],
                            "kwargs": task["kwargs"],
                            "worker": worker_name,
                            "time_start": task.get("time_start"),
                        }
                    )

            return active_tasks
        except Exception as e:
            logger.error(f"获取活跃任务失败: {e}")
            return []

    def get_worker_load(self) -> float:
        """
        获取Worker池的平均负载

        计算所有Worker的平均负载，用于判断系统整体负载情况。

        返回:
            float: 平均负载（0-1之间的值）
        """
        if not self._worker_stats:
            return 0.0

        total_load = sum(stats.get("load", 0) for stats in self._worker_stats.values())
        return total_load / len(self._worker_stats)

    def ping_workers(self) -> Dict[str, bool]:
        """
        Ping所有Worker

        检查所有Worker是否可响应。

        返回:
            Dict[str, bool]: Worker名称到响应状态的映射
        """
        try:
            # Ping所有Worker
            result = celery_app.control.ping()

            # 处理响应
            ping_results = {}
            for response in result:
                for worker_name, ping_response in response.items():
                    ping_results[worker_name] = ping_response == "pong"

            return ping_results
        except Exception as e:
            logger.error(f"Ping Worker失败: {e}")
            return {}


# 导出单例实例
worker_pool = WorkerPool()
