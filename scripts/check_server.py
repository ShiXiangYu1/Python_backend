#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
服务器检查脚本

该脚本用于检查API服务器是否正在运行，不依赖第三方库。
可用于在没有完整依赖环境的情况下验证服务可用性。
"""

import sys
import socket
import json
import time
import os
from datetime import datetime
from pathlib import Path

# 配置日志输出
def log(message, level="INFO"):
    """简单的日志输出函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def check_server(host="localhost", port=8000, timeout=5):
    """
    检查服务器是否可访问
    
    参数:
        host: 服务器主机名
        port: 服务器端口
        timeout: 连接超时时间(秒)
        
    返回:
        bool: 服务器是否可访问
    """
    log(f"检查服务器 {host}:{port} 是否可访问...")
    
    try:
        # 创建TCP套接字
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # 尝试连接
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            log(f"服务器 {host}:{port} 可访问")
            return True
        else:
            log(f"服务器 {host}:{port} 不可访问 (错误码: {result})", "ERROR")
            return False
    except socket.error as e:
        log(f"连接服务器时出错: {str(e)}", "ERROR")
        return False

def check_health_endpoint(host="localhost", port=8000, timeout=5):
    """
    检查健康检查端点是否正常
    
    参数:
        host: 服务器主机名
        port: 服务器端口
        timeout: 连接超时时间(秒)
        
    返回:
        bool: 健康检查是否正常
    """
    log(f"检查健康检查端点 http://{host}:{port}/api/v1/health...")
    
    try:
        # 创建TCP套接字
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # 连接服务器
        sock.connect((host, port))
        
        # 发送HTTP请求
        request = (
            f"GET /api/v1/health HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"User-Agent: check_server.py\r\n"
            f"Accept: application/json\r\n"
            f"Connection: close\r\n\r\n"
        )
        
        sock.sendall(request.encode())
        
        # 接收响应
        response = b""
        while True:
            data = sock.recv(4096)
            if not data:
                break
            response += data
        
        sock.close()
        
        # 解析响应
        response_str = response.decode('utf-8', errors='ignore')
        status_line = response_str.split('\r\n')[0]
        
        if "200 OK" in status_line:
            log("健康检查端点正常")
            return True
        else:
            log(f"健康检查端点返回非200状态: {status_line}", "ERROR")
            return False
    except Exception as e:
        log(f"请求健康检查端点时出错: {str(e)}", "ERROR")
        return False

def check_environment():
    """
    检查环境设置
    
    返回:
        dict: 环境信息
    """
    log("检查环境设置...")
    
    env_info = {
        "python_version": sys.version,
        "platform": sys.platform,
        "directory": os.getcwd(),
        "env_file_exists": os.path.exists(".env"),
        "database_file_exists": os.path.exists("app.db"),
        "uploads_dir_exists": os.path.exists("uploads"),
        "alembic_dir_exists": os.path.exists("alembic"),
    }
    
    for key, value in env_info.items():
        log(f"{key}: {value}")
    
    return env_info

def suggest_startup_methods():
    """
    建议可能的启动方法
    """
    log("\n推荐的启动方法:")
    
    # 检查各种可能的启动方法
    if os.path.exists("app.db") and os.path.exists(".env"):
        log("1. 使用Python直接启动 (如果已安装依赖):")
        log("   python -m uvicorn app.main:app --reload")
        
    if os.path.exists("Dockerfile") and os.path.exists("docker-compose.yml"):
        log("2. 使用Docker Compose启动:")
        log("   docker-compose up -d")
        
    log("3. 安装依赖后启动:")
    log("   pip install -r requirements.txt")
    log("   python -m uvicorn app.main:app --reload")

def main():
    """主函数"""
    log("开始检查API服务器...")
    
    # 检查环境
    env_info = check_environment()
    
    # 检查服务器可用性
    server_available = check_server()
    
    # 如果服务器可用，检查健康检查端点
    health_ok = False
    if server_available:
        health_ok = check_health_endpoint()
    
    # 总结结果
    log("\n检查结果:")
    log(f"环境检查: {'✅ 通过' if env_info.get('env_file_exists') and env_info.get('database_file_exists') else '⚠️ 警告'}")
    log(f"服务器可用性: {'✅ 通过' if server_available else '❌ 失败'}")
    log(f"健康检查: {'✅ 通过' if health_ok else '❌ 失败' if server_available else '❓ 未检查'}")
    
    # 如果服务器不可用，给出建议
    if not server_available:
        log("\n服务器未运行或不可访问。", "WARNING")
        suggest_startup_methods()
    
    return 0 if server_available and health_ok else 1

if __name__ == "__main__":
    sys.exit(main()) 