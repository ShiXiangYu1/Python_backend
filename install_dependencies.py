#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
依赖安装脚本

解决网络问题导致的依赖安装失败，通过尝试不同的镜像源和安装方式
自动处理依赖安装过程中的各种问题。
"""

import os
import sys
import subprocess
import argparse
import time
from datetime import datetime


def log_message(message, level="INFO"):
    """打印带有时间戳和日志级别的消息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def run_command(command, timeout=None):
    """
    运行命令并返回结果
    
    参数:
        command: 要执行的命令（字符串或列表）
        timeout: 超时时间（秒）
        
    返回:
        (returncode, stdout, stderr): 命令执行的返回代码、标准输出和标准错误
    """
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=isinstance(command, str),
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        process.kill()
        return 1, "", "命令执行超时"
    except Exception as e:
        return 1, "", f"命令执行出错: {str(e)}"


def check_pip():
    """检查pip是否可用，返回可用的pip命令（pip或pip3）"""
    commands = ["pip", "pip3"]
    
    for cmd in commands:
        returncode, stdout, _ = run_command([cmd, "--version"])
        if returncode == 0:
            log_message(f"找到可用的pip: {stdout.strip()}")
            return cmd
    
    log_message("未找到可用的pip，请先安装pip", "ERROR")
    return None


def check_python_version():
    """检查Python版本是否满足要求"""
    version_info = sys.version_info
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 8):
        log_message(f"Python版本 {sys.version} 过低，需要 Python 3.8 或更高版本", "ERROR")
        return False
    
    log_message(f"Python版本检查通过: {sys.version}")
    return True


def test_network_connection():
    """测试网络连接"""
    log_message("正在测试网络连接...")
    test_urls = [
        "https://pypi.org",
        "https://pypi.tuna.tsinghua.edu.cn",
        "https://mirrors.aliyun.com"
    ]
    
    working_urls = []
    
    for url in test_urls:
        returncode, _, _ = run_command(f"ping {url.replace('https://', '')}", timeout=5)
        if returncode == 0:
            working_urls.append(url)
            log_message(f"可以访问 {url}")
        else:
            log_message(f"无法访问 {url}", "WARNING")
    
    return working_urls


def install_with_pip(pip_command, requirements_file, index_url=None, trusted_host=None, timeout=300):
    """
    使用pip安装依赖
    
    参数:
        pip_command: pip命令 (pip 或 pip3)
        requirements_file: requirements.txt文件路径
        index_url: 指定的镜像源URL
        trusted_host: 信任的主机
        timeout: 命令超时时间（秒）
    
    返回:
        bool: 安装是否成功
    """
    cmd = [pip_command, "install", "-r", requirements_file]
    
    if index_url:
        cmd.extend(["-i", index_url])
    
    if trusted_host:
        cmd.extend(["--trusted-host", trusted_host])
    
    log_message(f"执行命令: {' '.join(cmd)}")
    
    returncode, stdout, stderr = run_command(cmd, timeout)
    
    if returncode == 0:
        log_message("依赖安装成功!")
        return True
    else:
        log_message(f"依赖安装失败: {stderr}", "ERROR")
        return False


def install_one_by_one(pip_command, requirements_file, index_url=None, trusted_host=None):
    """
    逐个安装依赖，跳过失败的包
    
    参数:
        pip_command: pip命令 (pip 或 pip3)
        requirements_file: requirements.txt文件路径
        index_url: 指定的镜像源URL
        trusted_host: 信任的主机
    
    返回:
        (list, list): 成功安装的包和失败安装的包
    """
    log_message("开始逐个安装依赖...")
    
    # 读取requirements.txt
    with open(requirements_file, "r") as f:
        lines = f.readlines()
    
    # 解析包名和版本
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            packages.append(line)
    
    succeeded = []
    failed = []
    
    for package in packages:
        cmd = [pip_command, "install", package]
        if index_url:
            cmd.extend(["-i", index_url])
        if trusted_host:
            cmd.extend(["--trusted-host", trusted_host])
        
        log_message(f"正在安装: {package}")
        returncode, _, stderr = run_command(cmd, timeout=120)
        
        if returncode == 0:
            succeeded.append(package)
            log_message(f"成功安装: {package}")
        else:
            failed.append(package)
            log_message(f"安装失败: {package} - {stderr}", "WARNING")
        
        # 短暂延迟，避免过于频繁的请求
        time.sleep(1)
    
    return succeeded, failed


def main():
    """主函数，处理依赖安装流程"""
    parser = argparse.ArgumentParser(description="Python项目依赖安装脚本")
    parser.add_argument("--requirements", default="requirements.txt", help="指定requirements.txt文件路径")
    parser.add_argument("--index-url", help="指定pip镜像源URL")
    parser.add_argument("--one-by-one", action="store_true", help="逐个安装依赖")
    parser.add_argument("--skip-network-test", action="store_true", help="跳过网络连接测试")
    args = parser.parse_args()
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查pip可用性
    pip_command = check_pip()
    if not pip_command:
        sys.exit(1)
    
    # 检查requirements.txt是否存在
    if not os.path.isfile(args.requirements):
        log_message(f"找不到requirements文件: {args.requirements}", "ERROR")
        sys.exit(1)
    
    # 测试网络连接
    working_urls = []
    if not args.skip_network_test:
        working_urls = test_network_connection()
        if not working_urls:
            log_message("所有测试的镜像源都无法访问，请检查网络连接", "ERROR")
            response = input("是否继续尝试安装？(y/n): ")
            if response.lower() != 'y':
                sys.exit(1)
    
    # 指定的镜像源
    mirrors = [
        ("默认PyPI", None, None),
        ("清华镜像", "https://pypi.tuna.tsinghua.edu.cn/simple", "pypi.tuna.tsinghua.edu.cn"),
        ("阿里云镜像", "https://mirrors.aliyun.com/pypi/simple/", "mirrors.aliyun.com"),
        ("豆瓣镜像", "https://pypi.doubanio.com/simple/", "pypi.doubanio.com"),
        ("华为云镜像", "https://repo.huaweicloud.com/repository/pypi/simple", "repo.huaweicloud.com")
    ]
    
    # 如果指定了镜像源
    if args.index_url:
        log_message(f"使用指定的镜像源: {args.index_url}")
        
        # 从URL提取主机名
        import re
        host_match = re.search(r"https?://([^/]+)", args.index_url)
        trusted_host = host_match.group(1) if host_match else None
        
        if args.one_by_one:
            succeeded, failed = install_one_by_one(pip_command, args.requirements, args.index_url, trusted_host)
            log_message(f"逐个安装结果: 成功 {len(succeeded)}/{len(succeeded) + len(failed)}, 失败 {len(failed)}")
            if failed:
                log_message(f"以下包安装失败: {', '.join(failed)}", "WARNING")
        else:
            success = install_with_pip(pip_command, args.requirements, args.index_url, trusted_host)
            if not success and not args.one_by_one:
                log_message("尝试逐个安装依赖...")
                succeeded, failed = install_one_by_one(pip_command, args.requirements, args.index_url, trusted_host)
                log_message(f"逐个安装结果: 成功 {len(succeeded)}/{len(succeeded) + len(failed)}, 失败 {len(failed)}")
        
        sys.exit(0)
    
    # 尝试不同的镜像源
    for mirror_name, mirror_url, trusted_host in mirrors:
        log_message(f"尝试使用{mirror_name}安装依赖...")
        
        if args.one_by_one:
            succeeded, failed = install_one_by_one(pip_command, args.requirements, mirror_url, trusted_host)
            log_message(f"逐个安装结果: 成功 {len(succeeded)}/{len(succeeded) + len(failed)}, 失败 {len(failed)}")
            if len(failed) == 0:
                log_message(f"使用{mirror_name}成功安装所有依赖!")
                break
        else:
            success = install_with_pip(pip_command, args.requirements, mirror_url, trusted_host)
            if success:
                log_message(f"使用{mirror_name}成功安装所有依赖!")
                break
            elif not args.one_by_one:
                log_message(f"使用{mirror_name}安装所有依赖失败，尝试逐个安装...")
                succeeded, failed = install_one_by_one(pip_command, args.requirements, mirror_url, trusted_host)
                log_message(f"逐个安装结果: 成功 {len(succeeded)}/{len(succeeded) + len(failed)}, 失败 {len(failed)}")
                if len(failed) == 0:
                    log_message(f"使用{mirror_name}成功安装所有依赖!")
                    break
        
        log_message(f"使用{mirror_name}安装依赖失败，尝试下一个镜像源...")
    
    log_message("依赖安装过程完成")


if __name__ == "__main__":
    main() 