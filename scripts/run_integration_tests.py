#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
运行集成测试脚本

启动应用并运行集成测试，验证系统各组件是否能够正常协同工作。
"""

import os
import sys
import time
import signal
import subprocess
import logging
import asyncio
from typing import Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("测试运行器")

# 应用进程
app_process: Optional[subprocess.Popen] = None


def signal_handler(sig, frame):
    """处理信号，确保在中断时清理资源"""
    logger.info("收到中断信号，正在清理...")
    cleanup()
    sys.exit(1)


def cleanup():
    """清理资源，停止应用进程"""
    global app_process
    if app_process:
        logger.info("正在停止应用进程...")
        app_process.terminate()
        try:
            app_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("应用进程未能及时停止，强制终止...")
            app_process.kill()
        app_process = None


def start_app():
    """启动应用"""
    global app_process
    logger.info("正在启动应用...")
    
    # 启动应用
    app_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 等待应用启动
    logger.info("等待应用启动...")
    time.sleep(5)  # 给应用一些启动时间
    
    # 检查应用是否成功启动
    if app_process.poll() is not None:
        stderr = app_process.stderr.read()
        logger.error(f"应用启动失败: {stderr}")
        return False
    
    logger.info("应用已启动")
    return True


def run_integration_tests():
    """运行集成测试"""
    logger.info("正在运行集成测试...")
    
    # 运行集成测试脚本
    result = subprocess.run(
        [sys.executable, os.path.join("scripts", "integration_test.py")],
        capture_output=True,
        text=True
    )
    
    # 输出测试结果
    logger.info(result.stdout)
    if result.stderr:
        logger.error(result.stderr)
    
    return result.returncode == 0


async def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动应用
        if not start_app():
            return 1
        
        # 运行集成测试
        tests_passed = run_integration_tests()
        
        if tests_passed:
            logger.info("🎉 集成测试全部通过！")
            return 0
        else:
            logger.error("❌ 集成测试失败！")
            return 1
    except Exception as e:
        logger.critical(f"测试过程中发生严重错误: {str(e)}")
        return 1
    finally:
        # 清理资源
        cleanup()


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 