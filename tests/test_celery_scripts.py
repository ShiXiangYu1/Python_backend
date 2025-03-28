#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Celery脚本单元测试模块

测试Celery Worker和Beat启动脚本的功能。
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入待测试模块
from scripts.celery_worker import parse_arguments as worker_parse_arguments
from scripts.celery_worker import start_worker, setup_environment as worker_setup_env
from scripts.celery_beat import parse_arguments as beat_parse_arguments
from scripts.celery_beat import start_beat, setup_environment as beat_setup_env
from scripts.celery_beat import create_schedule_dir


class TestCeleryWorkerScript(unittest.TestCase):
    """
    Celery Worker脚本测试类
    
    测试Celery Worker启动脚本的功能。
    """
    
    def setUp(self):
        """
        测试初始化
        
        在每个测试方法执行前设置测试环境。
        """
        # 保存原始环境变量
        self.original_environ = os.environ.copy()
    
    def tearDown(self):
        """
        测试清理
        
        在每个测试方法执行后恢复环境。
        """
        # 恢复原始环境变量
        os.environ.clear()
        os.environ.update(self.original_environ)
    
    def test_parse_arguments_defaults(self):
        """
        测试命令行参数解析默认值
        
        验证命令行参数解析函数返回的默认值是否符合预期。
        """
        # 设置模拟的命令行参数
        test_args = []
        
        with patch('sys.argv', ['celery_worker.py'] + test_args):
            args = worker_parse_arguments()
            
            # 验证默认值
            self.assertEqual(args.queues, 'default')
            self.assertEqual(args.loglevel, 'INFO')
            self.assertEqual(args.pool, 'prefork')
            self.assertFalse(args.beat)
    
    def test_parse_arguments_custom(self):
        """
        测试命令行参数解析自定义值
        
        验证命令行参数解析函数是否正确处理自定义参数。
        """
        # 设置模拟的命令行参数
        test_args = [
            '--queues', 'high_priority,default',
            '--concurrency', '4',
            '--loglevel', 'DEBUG',
            '--beat',
            '--pool', 'gevent'
        ]
        
        with patch('sys.argv', ['celery_worker.py'] + test_args):
            args = worker_parse_arguments()
            
            # 验证自定义值
            self.assertEqual(args.queues, 'high_priority,default')
            self.assertEqual(args.concurrency, 4)
            self.assertEqual(args.loglevel, 'DEBUG')
            self.assertTrue(args.beat)
            self.assertEqual(args.pool, 'gevent')
    
    @patch('app.celery_app.celery_app.worker_main')
    def test_start_worker(self, mock_worker_main):
        """
        测试启动Worker
        
        验证启动Worker函数是否正确调用了Celery的worker_main方法。
        
        参数:
            mock_worker_main: 模拟的Celery worker_main方法
        """
        # 创建模拟的参数对象
        args = MagicMock()
        args.queues = 'high_priority,default'
        args.concurrency = 4
        args.loglevel = 'DEBUG'
        args.beat = True
        args.pool = 'prefork'
        
        # 调用待测试函数
        start_worker(args)
        
        # 验证调用
        mock_worker_main.assert_called_once()
        
        # 验证传递给worker_main的参数
        call_args = mock_worker_main.call_args[0][0]
        self.assertIn('worker', call_args)
        self.assertIn('--queues', call_args)
        self.assertIn('high_priority,default', call_args)
        self.assertIn('--concurrency', call_args)
        self.assertIn('4', call_args)
        self.assertIn('--loglevel', call_args)
        self.assertIn('DEBUG', call_args)
        self.assertIn('--pool', call_args)
        self.assertIn('prefork', call_args)
        self.assertIn('--beat', call_args)
    
    def test_setup_environment(self):
        """
        测试环境变量设置
        
        验证环境变量设置函数是否正确设置了默认值。
        """
        # 清除相关环境变量
        if 'CELERY_BROKER_URL' in os.environ:
            del os.environ['CELERY_BROKER_URL']
        if 'CELERY_RESULT_BACKEND' in os.environ:
            del os.environ['CELERY_RESULT_BACKEND']
        
        # 调用待测试函数
        worker_setup_env()
        
        # 验证环境变量
        self.assertIn('CELERY_BROKER_URL', os.environ)
        self.assertEqual(os.environ['CELERY_BROKER_URL'], 'redis://localhost:6379/0')
        self.assertIn('CELERY_RESULT_BACKEND', os.environ)
        self.assertEqual(os.environ['CELERY_RESULT_BACKEND'], 'redis://localhost:6379/0')
        self.assertIn('PYTHONPATH', os.environ)


class TestCeleryBeatScript(unittest.TestCase):
    """
    Celery Beat脚本测试类
    
    测试Celery Beat启动脚本的功能。
    """
    
    def setUp(self):
        """
        测试初始化
        
        在每个测试方法执行前设置测试环境。
        """
        # 保存原始环境变量
        self.original_environ = os.environ.copy()
    
    def tearDown(self):
        """
        测试清理
        
        在每个测试方法执行后恢复环境。
        """
        # 恢复原始环境变量
        os.environ.clear()
        os.environ.update(self.original_environ)
    
    def test_parse_arguments_defaults(self):
        """
        测试命令行参数解析默认值
        
        验证命令行参数解析函数返回的默认值是否符合预期。
        """
        # 设置模拟的命令行参数
        test_args = []
        
        with patch('sys.argv', ['celery_beat.py'] + test_args):
            args = beat_parse_arguments()
            
            # 验证默认值
            self.assertEqual(args.loglevel, 'INFO')
            self.assertEqual(args.scheduler, 'celery.beat.PersistentScheduler')
            self.assertEqual(args.schedule, 'celerybeat-schedule')
            self.assertEqual(args.max_interval, 300)
    
    def test_parse_arguments_custom(self):
        """
        测试命令行参数解析自定义值
        
        验证命令行参数解析函数是否正确处理自定义参数。
        """
        # 设置模拟的命令行参数
        test_args = [
            '--loglevel', 'DEBUG',
            '--scheduler', 'celery.beat.DatabaseScheduler',
            '--schedule', '/var/tmp/celerybeat-schedule',
            '--max-interval', '600'
        ]
        
        with patch('sys.argv', ['celery_beat.py'] + test_args):
            args = beat_parse_arguments()
            
            # 验证自定义值
            self.assertEqual(args.loglevel, 'DEBUG')
            self.assertEqual(args.scheduler, 'celery.beat.DatabaseScheduler')
            self.assertEqual(args.schedule, '/var/tmp/celerybeat-schedule')
            self.assertEqual(args.max_interval, 600)
    
    @patch('app.celery_app.celery_app.start')
    def test_start_beat(self, mock_start):
        """
        测试启动Beat
        
        验证启动Beat函数是否正确调用了Celery的start方法。
        
        参数:
            mock_start: 模拟的Celery start方法
        """
        # 创建模拟的参数对象
        args = MagicMock()
        args.loglevel = 'DEBUG'
        args.scheduler = 'celery.beat.PersistentScheduler'
        args.schedule = 'celerybeat-schedule'
        args.max_interval = 300
        
        # 调用待测试函数
        start_beat(args)
        
        # 验证调用
        mock_start.assert_called_once()
        
        # 验证传递给start的参数
        call_args = mock_start.call_args[0][0]
        self.assertIn('beat', call_args)
        self.assertIn('--loglevel', call_args)
        self.assertIn('DEBUG', call_args)
        self.assertIn('--scheduler', call_args)
        self.assertIn('celery.beat.PersistentScheduler', call_args)
        self.assertIn('--schedule', call_args)
        self.assertIn('celerybeat-schedule', call_args)
        self.assertIn('--max-interval', call_args)
        self.assertIn('300', call_args)
    
    def test_setup_environment(self):
        """
        测试环境变量设置
        
        验证环境变量设置函数是否正确设置了默认值。
        """
        # 清除相关环境变量
        if 'CELERY_BROKER_URL' in os.environ:
            del os.environ['CELERY_BROKER_URL']
        if 'CELERY_RESULT_BACKEND' in os.environ:
            del os.environ['CELERY_RESULT_BACKEND']
        
        # 调用待测试函数
        beat_setup_env()
        
        # 验证环境变量
        self.assertIn('CELERY_BROKER_URL', os.environ)
        self.assertEqual(os.environ['CELERY_BROKER_URL'], 'redis://localhost:6379/0')
        self.assertIn('CELERY_RESULT_BACKEND', os.environ)
        self.assertEqual(os.environ['CELERY_RESULT_BACKEND'], 'redis://localhost:6379/0')
        self.assertIn('PYTHONPATH', os.environ)
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_create_schedule_dir_exists(self, mock_makedirs, mock_exists):
        """
        测试创建调度器目录（目录已存在）
        
        验证当目录已存在时，create_schedule_dir函数的行为是否正确。
        
        参数:
            mock_makedirs: 模拟的os.makedirs函数
            mock_exists: 模拟的os.path.exists函数
        """
        # 设置目录已存在
        mock_exists.return_value = True
        
        # 调用待测试函数
        create_schedule_dir('/tmp/celerybeat-schedule')
        
        # 验证不会尝试创建目录
        mock_makedirs.assert_not_called()
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_create_schedule_dir_not_exists(self, mock_makedirs, mock_exists):
        """
        测试创建调度器目录（目录不存在）
        
        验证当目录不存在时，create_schedule_dir函数是否正确创建目录。
        
        参数:
            mock_makedirs: 模拟的os.makedirs函数
            mock_exists: 模拟的os.path.exists函数
        """
        # 设置目录不存在
        mock_exists.return_value = False
        
        # 调用待测试函数
        create_schedule_dir('/tmp/celerybeat-schedule')
        
        # 验证尝试创建目录
        mock_makedirs.assert_called_once_with('/tmp', exist_ok=True)


if __name__ == '__main__':
    unittest.main() 