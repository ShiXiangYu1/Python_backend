#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Celery核心模块

提供Celery相关的辅助函数和类，包括日志配置、任务帮助类等。
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

from app.celery_app import celery_app


logger = logging.getLogger(__name__)


def init_celery_logging():
    """
    初始化Celery日志配置
    
    配置Celery的日志记录器，确保Celery的日志与应用其他部分的日志保持一致。
    
    这个函数应该在应用启动时被调用。
    """
    # 获取Celery日志记录器
    celery_logger = logging.getLogger('celery')
    
    # 设置日志级别
    celery_logger.setLevel(logging.INFO)
    
    # 如果没有处理程序，添加一个
    if not celery_logger.handlers:
        # 创建控制台处理程序
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        
        # 添加处理程序到日志记录器
        celery_logger.addHandler(console_handler)
    
    logger.info("Celery日志初始化完成")


class CeleryHelper:
    """
    Celery帮助类
    
    提供与Celery任务相关的辅助方法，简化任务操作。
    """
    
    @staticmethod
    def get_task_info(task_id: str) -> Dict[str, Any]:
        """
        获取任务信息
        
        从Celery中获取指定任务的当前状态和结果。
        
        参数:
            task_id: Celery任务ID
            
        返回:
            Dict[str, Any]: 包含任务状态和结果的字典
        """
        result = {
            "id": task_id,
            "status": "PENDING",
            "progress": 0,
            "result": None,
            "error": None
        }
        
        # 尝试获取AsyncResult
        try:
            task_result = celery_app.AsyncResult(task_id)
            
            # 获取任务状态
            result["status"] = task_result.status
            
            # 如果任务成功完成，获取结果
            if task_result.successful():
                result["result"] = task_result.result
                result["progress"] = 100
            
            # 如果任务失败，获取错误信息
            elif task_result.failed():
                result["error"] = str(task_result.result)
                
            # 如果任务正在执行，尝试获取进度信息
            elif task_result.status == "STARTED":
                # 尝试从元数据中获取进度
                meta = task_result.info
                if isinstance(meta, dict):
                    result["progress"] = meta.get("progress", 0)
                    result["status_message"] = meta.get("status_message", "")
        except Exception as e:
            logger.error(f"获取任务信息失败: {str(e)}")
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def revoke_task(task_id: str, terminate: bool = True) -> bool:
        """
        撤销任务
        
        撤销指定的Celery任务，可选择终止正在运行的任务。
        
        参数:
            task_id: Celery任务ID
            terminate: 是否终止正在运行的任务
            
        返回:
            bool: 操作是否成功
        """
        try:
            # 撤销任务
            celery_app.control.revoke(task_id, terminate=terminate, signal="SIGTERM")
            logger.info(f"已撤销任务: {task_id}")
            return True
        except Exception as e:
            logger.error(f"撤销任务失败: {str(e)}")
            return False
    
    @staticmethod
    def get_active_tasks() -> List[Dict[str, Any]]:
        """
        获取活跃任务列表
        
        获取所有活跃（正在执行）的Celery任务。
        
        返回:
            List[Dict[str, Any]]: 活跃任务列表
        """
        active_tasks = []
        
        try:
            # 获取活跃任务
            inspection = celery_app.control.inspect()
            active = inspection.active() or {}
            
            # 处理每个Worker的活跃任务
            for worker_name, tasks in active.items():
                for task in tasks:
                    active_tasks.append({
                        "id": task["id"],
                        "name": task["name"],
                        "args": task["args"],
                        "kwargs": task["kwargs"],
                        "worker": worker_name,
                        "time_start": task.get("time_start")
                    })
        except Exception as e:
            logger.error(f"获取活跃任务失败: {str(e)}")
        
        return active_tasks
    
    @staticmethod
    def get_task_queue_lengths() -> Dict[str, int]:
        """
        获取任务队列长度
        
        获取各个任务队列中等待执行的任务数量。
        
        返回:
            Dict[str, int]: 队列名称到任务数量的映射
        """
        queue_lengths = {}
        
        try:
            # 获取队列长度
            inspection = celery_app.control.inspect()
            reserved = inspection.reserved() or {}
            
            # 处理每个Worker的队列任务
            for worker_name, tasks in reserved.items():
                for task in tasks:
                    queue = task.get("delivery_info", {}).get("routing_key", "default")
                    queue_lengths[queue] = queue_lengths.get(queue, 0) + 1
        except Exception as e:
            logger.error(f"获取队列长度失败: {str(e)}")
        
        return queue_lengths
    
    @staticmethod
    def get_worker_stats() -> Dict[str, Dict[str, Any]]:
        """
        获取Worker统计信息
        
        获取所有Celery Worker的统计信息。
        
        返回:
            Dict[str, Dict[str, Any]]: Worker名称到统计信息的映射
        """
        worker_stats = {}
        
        try:
            # 获取Worker统计信息
            inspection = celery_app.control.inspect()
            stats = inspection.stats() or {}
            
            # 处理每个Worker的统计信息
            for worker_name, stat in stats.items():
                worker_stats[worker_name] = {
                    "processed": stat.get("total", {}).get("tasks", {}).get("total", 0),
                    "active": len(inspection.active().get(worker_name, [])),
                    "uptime": stat.get("uptime", 0),
                    "pid": stat.get("pid"),
                    "concurrency": stat.get("pool", {}).get("max-concurrency"),
                    "broker": stat.get("broker", {}).get("transport")
                }
        except Exception as e:
            logger.error(f"获取Worker统计信息失败: {str(e)}")
        
        return worker_stats


# 导出供其他模块使用的实例
celery_helper = CeleryHelper() 