#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Redis连接检查脚本

检查Redis服务器是否可访问，用于Celery任务系统的前置检查。
"""

import os
import sys
import time
from datetime import datetime


def log(message, level="INFO"):
    """打印带有时间戳和日志级别的消息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def check_redis_with_redis_py():
    """使用redis-py库检查Redis连接"""
    try:
        import redis
        log("使用redis-py检查Redis连接...")
        
        # 从环境变量或配置文件获取Redis连接信息
        redis_host = os.environ.get("REDIS_HOST", "localhost")
        redis_port = int(os.environ.get("REDIS_PORT", 6379))
        redis_password = os.environ.get("REDIS_PASSWORD", "")
        redis_db = int(os.environ.get("REDIS_DB", 0))
        
        # 创建Redis客户端
        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            db=redis_db,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        
        # 检查连接
        if client.ping():
            log(f"Redis连接成功: {redis_host}:{redis_port}/{redis_db}")
            client.close()
            return True
        else:
            log(f"Redis连接失败，无法执行PING命令", "ERROR")
            client.close()
            return False
            
    except ImportError:
        log("未安装redis-py库，跳过此方法检查", "WARNING")
        return None
    except Exception as e:
        log(f"Redis连接出错: {str(e)}", "ERROR")
        return False


def check_redis_with_socket():
    """使用socket库直接检查Redis端口是否开放"""
    try:
        import socket
        log("使用socket检查Redis端口...")
        
        redis_host = os.environ.get("REDIS_HOST", "localhost")
        redis_port = int(os.environ.get("REDIS_PORT", 6379))
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        result = sock.connect_ex((redis_host, redis_port))
        sock.close()
        
        if result == 0:
            log(f"Redis端口{redis_port}开放")
            return True
        else:
            log(f"Redis端口{redis_port}未开放", "ERROR")
            return False
            
    except Exception as e:
        log(f"检查Redis端口时出错: {str(e)}", "ERROR")
        return False


def check_redis_with_telnet():
    """使用telnetlib检查Redis连接"""
    try:
        import telnetlib
        log("使用telnet检查Redis连接...")
        
        redis_host = os.environ.get("REDIS_HOST", "localhost")
        redis_port = int(os.environ.get("REDIS_PORT", 6379))
        
        tn = telnetlib.Telnet(redis_host, redis_port, timeout=5)
        tn.close()
        
        log(f"Telnet连接Redis成功: {redis_host}:{redis_port}")
        return True
    except ImportError:
        log("未安装telnetlib库，跳过此方法检查", "WARNING")
        return None
    except Exception as e:
        log(f"Telnet连接Redis失败: {str(e)}", "ERROR")
        return False


def check_redis_for_celery():
    """检查Celery配置的Redis连接"""
    try:
        from celery.backends.redis import RedisBackend
        from celery.app.backends import get_backend_by_url
        
        log("检查Celery配置的Redis连接...")
        
        # 获取Celery配置的Redis URL
        broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
        result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
        
        log(f"Celery Broker URL: {broker_url}")
        log(f"Celery Result Backend: {result_backend}")
        
        # 尝试初始化后端连接
        if "redis" in result_backend:
            backend = get_backend_by_url(result_backend)
            if isinstance(backend, RedisBackend):
                client = backend.client
                if client.ping():
                    log("Celery Redis后端连接成功")
                    return True
                else:
                    log("Celery Redis后端连接失败", "ERROR")
                    return False
        
        log("Celery未使用Redis作为后端或无法验证连接", "WARNING")
        return None
        
    except ImportError:
        log("未安装celery库，跳过此方法检查", "WARNING")
        return None
    except Exception as e:
        log(f"检查Celery Redis连接时出错: {str(e)}", "ERROR")
        return False


def suggest_redis_installation():
    """提供Redis安装建议"""
    print("\n" + "="*60)
    print("Redis安装建议:")
    print("="*60)
    
    if sys.platform.startswith('win'):
        print("Windows系统:")
        print("1. 下载Redis for Windows: https://github.com/microsoftarchive/redis/releases")
        print("2. 安装并启动Redis服务")
        print("   或使用WSL安装Linux版Redis")
        print("3. 也可以使用Docker运行Redis容器：")
        print("   docker run --name redis -p 6379:6379 -d redis")
    elif sys.platform.startswith('linux'):
        print("Linux系统:")
        print("1. 安装Redis:")
        print("   Ubuntu/Debian: sudo apt update && sudo apt install redis-server")
        print("   CentOS/RHEL: sudo yum install redis")
        print("2. 启动Redis服务: sudo systemctl start redis")
        print("3. 或使用Docker: docker run --name redis -p 6379:6379 -d redis")
    elif sys.platform.startswith('darwin'):
        print("macOS系统:")
        print("1. 使用Homebrew安装: brew install redis")
        print("2. 启动Redis服务: brew services start redis")
        print("3. 或使用Docker: docker run --name redis -p 6379:6379 -d redis")
    
    print("\n后续步骤:")
    print("1. 安装Redis后，确保它在默认端口6379上运行")
    print("2. 在.env文件中设置正确的Redis连接信息")
    print("3. 重新运行此脚本验证连接")
    print("="*60)


def main():
    """主函数"""
    log("开始检查Redis连接...")
    
    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv()
        log("已加载.env文件中的环境变量")
    except ImportError:
        log("未安装python-dotenv库，无法加载.env文件", "WARNING")
    
    methods = [
        ("redis-py", check_redis_with_redis_py),
        ("socket", check_redis_with_socket),
        ("telnet", check_redis_with_telnet),
        ("celery", check_redis_for_celery)
    ]
    
    results = []
    for name, check_func in methods:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            log(f"{name}检查方法出错: {str(e)}", "ERROR")
            results.append((name, False))
        
        # 短暂延迟，避免连续请求
        time.sleep(0.5)
    
    # 结果汇总
    print("\n" + "="*60)
    print("Redis连接检查结果:")
    print("="*60)
    
    success_count = 0
    failure_count = 0
    skipped_count = 0
    
    for name, result in results:
        if result is True:
            status = "成功"
            success_count += 1
        elif result is False:
            status = "失败"
            failure_count += 1
        else:
            status = "跳过"
            skipped_count += 1
        
        print(f"{name:10}: {status}")
    
    print("-"*60)
    print(f"总计 {len(results)} 项检查: {success_count}成功, {failure_count}失败, {skipped_count}跳过")
    print("="*60)
    
    # 显示结论
    if success_count > 0:
        print("\n检查结论: Redis连接可用")
        print("可以启动Celery任务系统")
        return True
    else:
        print("\n检查结论: Redis连接不可用")
        suggest_redis_installation()
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log("检查被用户中断", "WARNING")
        sys.exit(130)
    except Exception as e:
        log(f"检查过程出错: {str(e)}", "ERROR")
        sys.exit(1) 