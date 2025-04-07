#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
常见任务模块

包含系统中通用的后台任务，如发送通知、生成报告等。
这些任务通常在默认队列中执行。
"""

import time
import uuid
import logging
import traceback
import asyncio
from typing import Dict, Any, Optional, List, Union, Callable
from functools import wraps

from celery import shared_task, Task, states
from celery.signals import task_prerun, task_postrun, task_failure, task_success
from celery.exceptions import SoftTimeLimitExceeded, Retry

from app.core.celery import celery_app
from app.models.task import TaskStatus
from app.services.redis_cache import redis_cache
from app.db.session import async_session, SessionLocal
from app.services.task import TaskService


logger = logging.getLogger(__name__)


class SQLAlchemyTask(Task):
    """
    自定义Celery任务基类

    扩展Celery的Task类，添加SQLAlchemy会话管理和任务状态更新功能。
    用于自动处理数据库会话和更新任务状态。
    """

    abstract = True

    # 默认重试策略
    default_retry_policy = {
        "max_retries": 3,  # 最大重试次数
        "interval_start": 0,  # 初始重试间隔（秒）
        "interval_step": 1,  # 每次重试增加的间隔（秒）
        "interval_max": 60,  # 最大重试间隔（秒）
        "retry_errors": None,  # 需要重试的错误类型，None表示所有错误
    }

    # 状态报告频率（秒）
    _status_report_interval = 5.0

    def __init__(self):
        """初始化任务基类"""
        self._last_update_time = 0.0
        self._start_time = 0.0
        self._metrics = {
            "total_time": 0.0,
            "db_time": 0.0,
            "processing_time": 0.0,
            "db_operations": 0,
        }

    def _update_retry_policy(self, retry_policy=None):
        """
        更新重试策略

        参数:
            retry_policy: 自定义重试策略，将与默认策略合并
        """
        policy = self.default_retry_policy.copy()
        if retry_policy:
            policy.update(retry_policy)

        for key, value in policy.items():
            setattr(self.request, key, value)

    def apply_async(self, args=None, kwargs=None, **options):
        """
        异步执行任务

        重写apply_async方法，添加自定义重试策略和性能监控。

        参数:
            args: 任务位置参数
            kwargs: 任务关键字参数
            **options: 其他选项

        返回:
            AsyncResult: 异步任务结果
        """
        # 更新重试策略
        retry_policy = options.pop("retry_policy", None)
        if retry_policy:
            self._update_retry_policy(retry_policy)

        # 如果未指定队列，根据任务优先级选择队列
        if "queue" not in options:
            priority = kwargs.get("priority", "normal")
            from app.celery_app import get_task_queue

            options["queue"] = get_task_queue(self.name, priority)

        return super().apply_async(args, kwargs, **options)

    def on_success(self, retval, task_id, args, kwargs):
        """
        任务成功回调

        在任务成功完成时更新任务状态和性能指标。

        参数:
            retval: 任务返回值
            task_id: 任务ID
            args: 任务位置参数
            kwargs: 任务关键字参数
        """
        # 记录性能指标
        self._metrics["total_time"] = time.time() - self._start_time

        # 如果返回值是字典且包含result字段，使用它作为任务结果
        result = retval
        if isinstance(retval, dict) and "result" in retval:
            result = retval

        # 如果包含db_task_id参数，更新任务状态
        db_task_id = kwargs.get("task_id")
        if db_task_id:
            # 异步更新任务状态
            self._update_db_task_status(
                db_task_id, TaskStatus.SUCCEEDED, progress=100, result=result
            )

            # 缓存任务结果
            if result:
                redis_cache.cache_task_result(db_task_id, result)

        # 记录性能指标
        logger.info(
            f"任务 {self.name}[{task_id}] 成功完成，耗时: {self._metrics['total_time']:.2f}秒，"
            f"数据库操作: {self._metrics['db_time']:.2f}秒 ({self._metrics['db_operations']}次操作)"
        )

        return super().on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        任务失败回调

        在任务失败时更新任务状态和错误信息。

        参数:
            exc: 异常对象
            task_id: 任务ID
            args: 任务位置参数
            kwargs: 任务关键字参数
            einfo: 异常信息
        """
        # 记录性能指标
        self._metrics["total_time"] = time.time() - self._start_time

        # 格式化错误信息
        error_info = {
            "error": str(exc),
            "traceback": einfo.traceback if einfo else None,
            "time": time.time(),
        }

        # 如果包含db_task_id参数，更新任务状态
        db_task_id = kwargs.get("task_id")
        if db_task_id:
            # 如果是重试异常，更新为PENDING状态
            status = TaskStatus.FAILED
            if isinstance(exc, Retry):
                status = TaskStatus.PENDING
                error_info["retry_count"] = self.request.retries
                error_info["max_retries"] = self.request.max_retries

            # 异步更新任务状态
            self._update_db_task_status(db_task_id, status, error=error_info)

        # 记录错误日志
        logger.error(
            f"任务 {self.name}[{task_id}] 执行失败: {exc}，"
            f"耗时: {self._metrics['total_time']:.2f}秒"
        )

        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def before_start(self, task_id, args, kwargs):
        """
        任务启动前回调

        在任务开始执行前初始化计时器和性能指标。

        参数:
            task_id: 任务ID
            args: 任务位置参数
            kwargs: 任务关键字参数
        """
        # 初始化计时器
        self._start_time = time.time()
        self._last_update_time = self._start_time

        # 重置性能指标
        self._metrics = {
            "total_time": 0.0,
            "db_time": 0.0,
            "processing_time": 0.0,
            "db_operations": 0,
        }

        # 如果包含db_task_id参数，更新任务状态为RUNNING
        db_task_id = kwargs.get("task_id")
        if db_task_id:
            self._update_db_task_status(
                db_task_id,
                TaskStatus.RUNNING,
                progress=0,
                result={"status": "started", "message": "任务开始执行"},
            )

        super().before_start(task_id, args, kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        任务返回后回调

        在任务返回后清理资源。

        参数:
            status: 任务状态
            retval: 任务返回值
            task_id: 任务ID
            args: 任务位置参数
            kwargs: 任务关键字参数
            einfo: 异常信息
        """
        # 记录日志
        logger.debug(f"任务 {self.name}[{task_id}] 已返回，状态: {status}")

        # 关闭数据库会话
        try:
            db = SessionLocal()
            db.close()
        except Exception as e:
            logger.error(f"关闭数据库会话失败: {e}")

        super().after_return(status, retval, task_id, args, kwargs, einfo)

    def update_progress(
        self, db_task_id: str, progress: int, result: Any = None
    ) -> bool:
        """
        更新任务进度

        在任务执行过程中周期性地更新进度和状态。
        为避免频繁更新数据库，使用最小间隔限制更新频率。

        参数:
            db_task_id: 数据库中的任务ID
            progress: 任务进度（0-100）
            result: 阶段性结果

        返回:
            bool: 是否成功更新
        """
        # 防止频繁更新，限制更新频率
        current_time = time.time()
        if current_time - self._last_update_time < self._status_report_interval:
            return False

        # 更新时间戳
        self._last_update_time = current_time

        # 确保进度在有效范围内
        progress = min(max(progress, 0), 100)

        # 准备结果数据
        status_data = {
            "progress": progress,
            "time": current_time,
            "elapsed": current_time - self._start_time,
        }

        if result:
            status_data.update(result if isinstance(result, dict) else {"data": result})

        # 异步更新任务状态
        self._update_db_task_status(
            db_task_id, TaskStatus.RUNNING, progress=progress, result=status_data
        )

        # 记录日志
        logger.debug(f"任务进度更新: {progress}%，耗时: {status_data['elapsed']:.2f}秒")

        return True

    def _update_db_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: Optional[int] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        更新任务状态

        更新数据库中任务的状态、进度和结果信息。

        参数:
            task_id: 任务ID
            status: 新的任务状态
            progress: 任务进度（0-100）
            result: 任务结果数据
            error: 任务错误信息
        """
        try:
            # 优先使用缓存更新任务状态
            task_data = {
                "status": status.value if hasattr(status, "value") else status,
                "updated_at": time.time(),
            }

            if progress is not None:
                task_data["progress"] = progress

            if result is not None:
                task_data["result"] = result

            if error is not None:
                task_data["error"] = error

            # 缓存任务状态
            redis_cache.cache_task_status(task_id, task_data)

            # 使用同步方式更新数据库
            # 创建一个新的事件循环来运行异步代码
            def run_async_update():
                db_time_start = time.time()
                self._metrics["db_operations"] += 1

                # 创建一个新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # 定义异步更新函数
                async def update_status():
                    async with async_session() as session:
                        # 创建任务服务
                        task_service = TaskService()

                        # 更新任务状态
                        await task_service.update_task_status(
                            db=session,
                            task_id=uuid.UUID(task_id),
                            status=status,
                            progress=progress,
                            result=result,
                            error=error,
                        )

                # 运行异步函数并关闭循环
                try:
                    loop.run_until_complete(update_status())
                finally:
                    loop.close()

                # 记录数据库操作时间
                self._metrics["db_time"] += time.time() - db_time_start

            # 执行同步封装的异步更新
            run_async_update()

        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")

    def batch_process(
        self,
        items: List[Any],
        process_func: Callable,
        batch_size: int = 100,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        批量处理

        对大量数据进行批处理，定期更新进度和状态。

        参数:
            items: 要处理的数据项列表
            process_func: 处理单个数据项的函数，参数为(item, index)
            batch_size: 每批处理的数据项数量
            task_id: 数据库中的任务ID

        返回:
            Dict[str, Any]: 包含处理结果和统计信息的字典
        """
        total_items = len(items)
        results = []
        errors = []
        start_time = time.time()

        # 处理空列表情况
        if total_items == 0:
            logger.warning("批处理接收到空列表，跳过处理")
            return {
                "success": True,
                "processed": 0,
                "errors": 0,
                "time": 0,
                "results": [],
                "error_details": [],
            }

        # 初始化进度
        if task_id:
            self.update_progress(
                task_id, 0, {"total_items": total_items, "batch_size": batch_size}
            )

        # 分批处理
        for i in range(0, total_items, batch_size):
            batch = items[i : i + batch_size]
            batch_results = []

            # 处理当前批次
            for idx, item in enumerate(batch):
                try:
                    # 处理单个项目
                    result = process_func(item, i + idx)
                    batch_results.append(result)
                except Exception as e:
                    # 记录错误
                    error_info = {
                        "index": i + idx,
                        "item": item,
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    }
                    errors.append(error_info)
                    logger.error(f"处理项目 {i + idx} 失败: {e}")

            # 添加批次结果
            results.extend(batch_results)

            # 更新进度
            progress = min(int((i + len(batch)) / total_items * 100), 99)
            if task_id:
                self.update_progress(
                    task_id,
                    progress,
                    {
                        "processed": i + len(batch),
                        "total": total_items,
                        "errors": len(errors),
                        "current_batch": i // batch_size + 1,
                        "total_batches": (total_items + batch_size - 1) // batch_size,
                    },
                )

        # 计算处理时间
        elapsed_time = time.time() - start_time

        # 生成结果
        result = {
            "success": len(errors) == 0,
            "processed": total_items,
            "errors": len(errors),
            "time": elapsed_time,
            "results": results,
            "error_details": errors[:10],  # 只返回前10个错误详情
        }

        # 最终更新进度
        if task_id:
            self.update_progress(task_id, 100, result)

        return result


@task_prerun.connect
def on_task_prerun(task_id=None, task=None, args=None, kwargs=None, **kw):
    """
    任务开始前执行的信号处理函数

    记录任务开始执行的日志，用于任务跟踪和调试。

    参数:
        task_id: Celery任务ID
        task: 任务对象
        args: 任务位置参数
        kwargs: 任务关键字参数
    """
    logger.info(f"任务开始执行: {task.name}[{task_id}]")

    # 使用任务基类的before_start方法处理任务开始逻辑
    if hasattr(task, "before_start"):
        task.before_start(task_id, args, kwargs)


@task_success.connect
def on_task_success(sender=None, result=None, **kwargs):
    """
    任务成功完成的信号处理函数

    记录任务成功完成的日志。

    参数:
        sender: 发送信号的任务
        result: 任务结果
        kwargs: 其他参数
    """
    task_id = kwargs.get("task_id")
    logger.info(f"任务成功完成: {sender.name}[{task_id}]")


@task_failure.connect
def on_task_failure(sender=None, exception=None, args=None, kwargs=None, **kw):
    """
    任务失败的信号处理函数

    记录任务失败的日志和异常信息。

    参数:
        sender: 发送信号的任务
        exception: 导致任务失败的异常
        args: 任务位置参数
        kwargs: 任务关键字参数
    """
    task_id = kw.get("task_id")
    logger.error(f"任务执行失败: {sender.name}[{task_id}], 错误: {exception}")


@task_postrun.connect
def on_task_postrun(task_id=None, task=None, args=None, kwargs=None, **kw):
    """
    任务完成后执行的信号处理函数

    记录任务结束的日志，用于任务跟踪和调试。

    参数:
        task_id: Celery任务ID
        task: 任务对象
        args: 任务位置参数
        kwargs: 任务关键字参数
    """
    state = kw.get("state")
    logger.info(f"任务执行完成: {task.name}[{task_id}], 状态: {state}")


def auto_retry(max_retries=3, retry_backoff=True, retry_jitter=True):
    """
    自动重试装饰器

    为任务提供自动重试功能，支持指数退避和抖动。

    参数:
        max_retries: 最大重试次数
        retry_backoff: 是否使用指数退避
        retry_jitter: 是否使用随机抖动

    返回:
        Callable: 装饰器函数
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SoftTimeLimitExceeded as e:
                # 超时异常不重试
                logger.error(f"任务超时: {e}")
                raise
            except Exception as e:
                # 获取任务对象
                task = (
                    wrapper.task
                    if hasattr(wrapper, "task")
                    else celery_app.current_task
                )

                if task is None:
                    # 非Celery任务环境
                    logger.error(f"任务执行失败，无法重试: {e}")
                    raise

                # 获取当前重试次数
                retries = task.request.retries

                if retries >= max_retries:
                    # 达到最大重试次数
                    logger.error(f"任务达到最大重试次数 ({max_retries})，放弃重试: {e}")
                    raise

                # 计算重试延迟
                retry_delay = 1
                if retry_backoff:
                    # 指数退避: 1, 2, 4, 8, 16, ...
                    retry_delay = 2**retries

                if retry_jitter:
                    # 添加随机抖动 (±30%)
                    import random

                    jitter = random.uniform(0.7, 1.3)
                    retry_delay *= jitter

                logger.info(
                    f"任务将在 {retry_delay:.2f} 秒后重试 (尝试 {retries + 1}/{max_retries})"
                )

                # 重试任务
                raise task.retry(exc=e, countdown=retry_delay, max_retries=max_retries)

        return wrapper

    return decorator


@shared_task(bind=True, base=SQLAlchemyTask)
@auto_retry(max_retries=3)
def long_running_task(
    self, seconds: int = 10, task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    长时间运行的示例任务

    用于测试任务进度更新和状态跟踪的示例任务。
    每秒更新一次进度，直到指定的时间结束。

    参数:
        seconds: 任务运行的总秒数
        task_id: 数据库中的任务ID

    返回:
        Dict[str, Any]: 包含任务执行结果的字典
    """
    # 将秒数限制在1到3600之间
    seconds = min(max(seconds, 1), 3600)

    logger.info(f"开始执行长时间运行的任务，持续时间: {seconds}秒")

    # 模拟长时间运行的任务
    start_time = time.time()

    for i in range(seconds):
        # 计算进度
        progress = int((i + 1) / seconds * 100)

        # 更新任务状态
        if task_id:
            self.update_progress(
                task_id,
                progress,
                {
                    "current_step": i + 1,
                    "total_steps": seconds,
                    "message": f"处理步骤 {i + 1}/{seconds}",
                },
            )

        # 模拟处理
        time.sleep(1)

    # 计算总耗时
    total_time = time.time() - start_time

    # 返回结果
    result = {
        "message": f"任务成功完成，处理了 {seconds} 个步骤",
        "duration": total_time,
        "steps_processed": seconds,
    }

    return result


@shared_task(bind=True, base=SQLAlchemyTask)
@auto_retry(max_retries=2)
def batch_process_items(
    self, items: List[Any], task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    批量处理数据项

    批量处理数据项，支持进度跟踪和错误处理。

    参数:
        items: 要处理的数据项列表
        task_id: 数据库中的任务ID

    返回:
        Dict[str, Any]: 包含处理结果的字典
    """
    logger.info(f"开始批量处理 {len(items)} 个数据项")

    # 定义单个项目的处理函数
    def process_item(item, index):
        # 模拟处理单个项目
        time.sleep(0.1)  # 模拟处理时间
        return {"index": index, "value": item, "processed": True}

    # 使用批处理函数
    result = self.batch_process(items, process_item, batch_size=50, task_id=task_id)

    logger.info(f"批量处理完成，处理了 {result['processed']} 个项目，有 {result['errors']} 个错误")

    return result


@shared_task
def send_notification(
    user_id: str, message: str, notification_type: str = "info"
) -> Dict[str, Any]:
    """
    发送通知

    发送通知给指定用户。

    参数:
        user_id: 用户ID
        message: 通知消息
        notification_type: 通知类型 (info, warning, error)

    返回:
        Dict[str, Any]: 发送结果
    """
    logger.info(f"发送 {notification_type} 通知给用户 {user_id}: {message}")

    # 在这里实现实际的通知发送逻辑
    # 例如，发送电子邮件、推送通知等

    # 模拟发送过程
    time.sleep(0.5)

    return {
        "success": True,
        "user_id": user_id,
        "message": message,
        "type": notification_type,
        "sent_at": time.time(),
    }


@shared_task(bind=True, base=SQLAlchemyTask)
@auto_retry(max_retries=3, retry_backoff=True)
def cleanup_old_data(
    self, days: int = 30, task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    清理旧数据

    清理系统中指定天数之前的旧数据。

    参数:
        days: 清理多少天之前的数据
        task_id: 数据库中的任务ID

    返回:
        Dict[str, Any]: 清理结果
    """
    logger.info(f"开始清理 {days} 天之前的旧数据")

    # 如果有任务ID，更新初始进度
    if task_id:
        self.update_progress(task_id, 10, {"message": "开始清理旧数据"})

    # 在这里实现实际的数据清理逻辑
    # 例如，删除旧日志、临时文件等

    # 模拟清理过程
    time.sleep(2)

    # 更新进度到50%
    if task_id:
        self.update_progress(task_id, 50, {"message": "清理临时文件"})

    # 继续模拟清理
    time.sleep(1)

    # 更新进度到80%
    if task_id:
        self.update_progress(task_id, 80, {"message": "清理数据库记录"})

    # 完成清理
    time.sleep(1)

    result = {
        "message": f"成功清理了 {days} 天之前的旧数据",
        "days_cleaned": days,
        "files_removed": 15,  # 示例数据
        "records_deleted": 120,  # 示例数据
        "space_freed": "1.2 GB",  # 示例数据
    }

    # 完成任务
    if task_id:
        self.update_progress(task_id, 100, result)

    logger.info(f"旧数据清理完成: {result}")

    return result
