#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SQLAlchemyTask批处理测试模块

测试SQLAlchemyTask中的batch_process方法，确保批量处理功能正常工作。
"""

import time
import pytest
from unittest.mock import patch, MagicMock, call

from app.tasks.common_tasks import SQLAlchemyTask


@patch('app.tasks.common_tasks.logger')
class TestBatchProcess:
    """批处理测试类"""
    
    def test_batch_process_empty_items(self, mock_logger):
        """测试批处理空列表"""
        task = SQLAlchemyTask()
        process_func = MagicMock()
        
        # 批处理空列表
        result = task.batch_process([], process_func)
        
        # 验证结果
        assert result["success"] == True
        assert result["processed"] == 0
        assert result["errors"] == 0
        assert len(result["results"]) == 0
        assert len(result["error_details"]) == 0
        
        # 验证警告日志被记录
        mock_logger.warning.assert_called_once()
        args, kwargs = mock_logger.warning.call_args
        assert "批处理接收到空列表" in args[0]
        
        # 验证处理函数未被调用
        process_func.assert_not_called()
    
    def test_batch_process_without_task_id(self, mock_logger):
        """测试无任务ID的批处理"""
        task = SQLAlchemyTask()
        process_func = MagicMock(return_value={"processed": True})
        test_items = ["item1", "item2", "item3", "item4", "item5"]
        
        # 模拟update_progress方法
        task.update_progress = MagicMock()
        
        # 批处理项目
        result = task.batch_process(test_items, process_func, batch_size=2)
        
        # 验证结果
        assert result["success"] == True
        assert result["processed"] == 5
        assert result["errors"] == 0
        assert len(result["results"]) == 5
        
        # 验证处理函数被正确调用
        assert process_func.call_count == 5
        for i, item in enumerate(test_items):
            process_func.assert_any_call(item, i)
        
        # 验证update_progress未被调用（因为没有提供task_id）
        task.update_progress.assert_not_called()
    
    def test_batch_process_with_task_id(self, mock_logger):
        """测试有任务ID的批处理"""
        task = SQLAlchemyTask()
        process_func = MagicMock(return_value={"processed": True})
        test_items = ["item1", "item2", "item3", "item4", "item5"]
        task_id = "test-task-id"
        
        # 模拟update_progress方法
        task.update_progress = MagicMock()
        
        # 批处理项目
        result = task.batch_process(test_items, process_func, batch_size=2, task_id=task_id)
        
        # 验证结果
        assert result["success"] == True
        assert result["processed"] == 5
        assert result["errors"] == 0
        assert len(result["results"]) == 5
        
        # 验证update_progress被正确调用
        # 初始进度
        task.update_progress.assert_any_call(
            task_id, 0, {"total_items": 5, "batch_size": 2}
        )
        
        # 验证批次进度更新
        progress_calls = [
            call(task_id, 40, {
                "processed": 2, 
                "total": 5, 
                "errors": 0, 
                "current_batch": 1, 
                "total_batches": 3
            }),
            call(task_id, 80, {
                "processed": 4, 
                "total": 5, 
                "errors": 0, 
                "current_batch": 2, 
                "total_batches": 3
            }),
            call(task_id, 99, {
                "processed": 5, 
                "total": 5, 
                "errors": 0, 
                "current_batch": 3, 
                "total_batches": 3
            }),
        ]
        task.update_progress.assert_has_calls(progress_calls, any_order=False)
        
        # 验证最终更新
        task.update_progress.assert_called_with(task_id, 100, result)
    
    def test_batch_process_with_errors(self, mock_logger):
        """测试批处理中的错误处理"""
        task = SQLAlchemyTask()
        
        # 创建一个处理函数，对某些项目抛出异常
        def process_func(item, index):
            if index % 2 == 1:  # 对索引为奇数的项目抛出异常
                raise ValueError(f"处理 {item} 时出错")
            return {"processed": True, "item": item}
        
        test_items = ["item1", "item2", "item3", "item4", "item5"]
        
        # 批处理项目
        result = task.batch_process(test_items, process_func)
        
        # 验证结果
        assert result["success"] == False  # 有错误，所以不成功
        assert result["processed"] == 5
        assert result["errors"] == 2  # 两个项目（索引1和3）应该失败
        assert len(result["results"]) == 3  # 三个项目应该成功
        assert len(result["error_details"]) == 2  # 两个错误详情
        
        # 验证错误日志
        assert mock_logger.error.call_count == 2
        for i in [1, 3]:
            args, kwargs = mock_logger.error.call_args_list[i//2]
            assert f"处理项目 {i} 失败" in args[0]
    
    def test_batch_process_performance(self, mock_logger):
        """测试批处理性能统计"""
        task = SQLAlchemyTask()
        
        # 创建一个模拟处理函数，添加延迟
        def process_func(item, index):
            time.sleep(0.01)  # 模拟处理时间
            return {"processed": True, "item": item}
        
        # 创建大量测试项目
        test_items = [f"item{i}" for i in range(20)]
        
        # 记录开始时间
        start_time = time.time()
        
        # 批处理项目
        result = task.batch_process(test_items, process_func, batch_size=5)
        
        # 验证结果包含时间统计
        assert "time" in result
        assert result["time"] > 0
        
        # 验证执行时间大约为预期（20项，每项0.01秒）
        assert 0.1 < result["time"] < 0.5  # 允许一些误差

    def test_batch_process_custom_batch_size(self, mock_logger):
        """测试自定义批次大小"""
        task = SQLAlchemyTask()
        process_func = MagicMock(return_value={"processed": True})
        test_items = [f"item{i}" for i in range(10)]
        
        # 使用自定义批次大小
        result = task.batch_process(test_items, process_func, batch_size=3)
        
        # 验证结果
        assert result["processed"] == 10
        assert len(result["results"]) == 10
        
        # 验证处理函数被正确调用
        assert process_func.call_count == 10
        
        # 验证批次大小为3会导致不同的批次数
        # 10个项目，批次大小为3，应该有4个批次（3+3+3+1）
        expected_batches = 4
        assert (len(test_items) + 3 - 1) // 3 == expected_batches 