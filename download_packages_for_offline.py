#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
依赖包下载脚本

用于在网络连接良好的环境中下载所有依赖包到本地，
然后可以将下载的包传输到网络受限环境中进行离线安装。
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


def parse_requirements(requirements_file):
    """
    解析requirements.txt文件
    
    参数:
        requirements_file: requirements.txt文件路径
        
    返回:
        list: 有效的依赖包列表
    """
    try:
        with open(requirements_file, "r") as f:
            lines = f.readlines()
        
        packages = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                packages.append(line)
        
        return packages
    except Exception as e:
        log_message(f"解析requirements.txt出错: {str(e)}", "ERROR")
        return []


def download_packages(pip_command, packages, output_dir, index_url=None, trusted_host=None):
    """
    下载依赖包到本地
    
    参数:
        pip_command: pip命令 (pip 或 pip3)
        packages: 要下载的包列表
        output_dir: 输出目录
        index_url: 指定的镜像源URL
        trusted_host: 信任的主机
        
    返回:
        (list, list): 成功下载的包和失败下载的包
    """
    log_message(f"开始下载依赖包到 {output_dir}...")
    
    # 创建输出目录（如果不存在）
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            log_message(f"创建输出目录: {output_dir}")
        except Exception as e:
            log_message(f"创建输出目录失败: {str(e)}", "ERROR")
            return [], packages
    
    succeeded = []
    failed = []
    
    for package in packages:
        log_message(f"下载包: {package}")
        
        cmd = [pip_command, "download", package, "-d", output_dir]
        
        if index_url:
            cmd.extend(["-i", index_url])
        
        if trusted_host:
            cmd.extend(["--trusted-host", trusted_host])
        
        returncode, stdout, stderr = run_command(cmd, timeout=300)
        
        if returncode == 0:
            succeeded.append(package)
            log_message(f"成功下载: {package}")
        else:
            failed.append(package)
            log_message(f"下载失败: {package}", "WARNING")
            log_message(f"错误信息: {stderr}", "WARNING")
        
        # 短暂延迟，避免过于频繁的请求
        time.sleep(1)
    
    return succeeded, failed


def create_offline_install_script(output_dir, bat_file=True, sh_file=True):
    """
    创建离线安装脚本
    
    参数:
        output_dir: 包含离线包的目录
        bat_file: 是否创建Windows批处理脚本
        sh_file: 是否创建Linux/Mac shell脚本
    """
    if bat_file:
        bat_path = os.path.join(output_dir, "install_offline.bat")
        with open(bat_path, "w") as f:
            f.write("@echo off\n")
            f.write("echo 开始离线安装依赖包...\n")
            f.write("echo.\n\n")
            f.write(":: 检查pip是否可用\n")
            f.write("pip --version > nul 2>&1\n")
            f.write("if %errorlevel% NEQ 0 (\n")
            f.write("    echo 未找到pip，尝试使用pip3...\n")
            f.write("    pip3 --version > nul 2>&1\n")
            f.write("    if %errorlevel% NEQ 0 (\n")
            f.write("        echo 错误: 未找到pip或pip3，请确保已安装Python并添加到PATH环境变量中\n")
            f.write("        pause\n")
            f.write("        exit /b 1\n")
            f.write("    ) else (\n")
            f.write("        set PIP_CMD=pip3\n")
            f.write("    )\n")
            f.write(") else (\n")
            f.write("    set PIP_CMD=pip\n")
            f.write(")\n\n")
            f.write("echo 使用 %PIP_CMD% 安装依赖...\n")
            f.write("echo.\n\n")
            f.write("for %%f in (*.whl *.tar.gz *.zip) do (\n")
            f.write("    echo 安装: %%f\n")
            f.write("    %PIP_CMD% install \"%%f\"\n")
            f.write("    if %errorlevel% NEQ 0 (\n")
            f.write("        echo 警告: 安装 %%f 失败\n")
            f.write("    ) else (\n")
            f.write("        echo 成功安装: %%f\n")
            f.write("    )\n")
            f.write(")\n\n")
            f.write("echo.\n")
            f.write("echo 安装过程已完成。\n")
            f.write("pause\n")
        
        log_message(f"创建Windows离线安装脚本: {bat_path}")
    
    if sh_file:
        sh_path = os.path.join(output_dir, "install_offline.sh")
        with open(sh_path, "w") as f:
            f.write("#!/bin/bash\n\n")
            f.write("echo '开始离线安装依赖包...'\n")
            f.write("echo\n\n")
            f.write("# 检查pip是否可用\n")
            f.write("if command -v pip >/dev/null 2>&1; then\n")
            f.write("    PIP_CMD=pip\n")
            f.write("elif command -v pip3 >/dev/null 2>&1; then\n")
            f.write("    PIP_CMD=pip3\n")
            f.write("else\n")
            f.write("    echo '错误: 未找到pip或pip3，请确保已安装Python'\n")
            f.write("    exit 1\n")
            f.write("fi\n\n")
            f.write("echo \"使用 $PIP_CMD 安装依赖...\"\n")
            f.write("echo\n\n")
            f.write("for pkg in *.whl *.tar.gz *.zip; do\n")
            f.write("    # 跳过未匹配到文件的通配符\n")
            f.write("    [ -e \"$pkg\" ] || continue\n\n")
            f.write("    echo \"安装: $pkg\"\n")
            f.write("    \"$PIP_CMD\" install \"$pkg\"\n")
            f.write("    if [ $? -ne 0 ]; then\n")
            f.write("        echo \"警告: 安装 $pkg 失败\"\n")
            f.write("    else\n")
            f.write("        echo \"成功安装: $pkg\"\n")
            f.write("    fi\n")
            f.write("done\n\n")
            f.write("echo\n")
            f.write("echo '安装过程已完成。'\n")
        
        # 设置shell脚本的执行权限
        try:
            os.chmod(sh_path, 0o755)
        except:
            log_message("无法设置shell脚本的执行权限", "WARNING")
        
        log_message(f"创建Linux/Mac离线安装脚本: {sh_path}")


def create_readme(output_dir, succeeded, failed):
    """
    创建README文件
    
    参数:
        output_dir: 输出目录
        succeeded: 成功下载的包列表
        failed: 下载失败的包列表
    """
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write("# Python后端项目离线依赖包\n\n")
        f.write("此目录包含Python后端项目所需的依赖包，用于在网络受限环境中安装。\n\n")
        
        f.write("## 使用方法\n\n")
        f.write("### Windows\n\n")
        f.write("1. 双击运行`install_offline.bat`\n\n")
        
        f.write("### Linux/Mac\n\n")
        f.write("1. 打开终端，进入此目录\n")
        f.write("2. 执行命令: `bash install_offline.sh`或`./install_offline.sh`\n\n")
        
        f.write("## 包含的依赖包\n\n")
        f.write(f"总计下载成功: {len(succeeded)} 个包\n\n")
        
        if succeeded:
            f.write("### 成功下载的包\n\n")
            for package in succeeded:
                f.write(f"- {package}\n")
            f.write("\n")
        
        if failed:
            f.write("### 下载失败的包\n\n")
            f.write("以下包下载失败，您可能需要手动安装:\n\n")
            for package in failed:
                f.write(f"- {package}\n")
            f.write("\n")
        
        f.write("## 注意事项\n\n")
        f.write("1. 这些包是为特定版本的Python下载的，请确保您使用的Python版本与下载时使用的版本相同或兼容\n")
        f.write(f"2. 下载时使用的Python版本: {sys.version}\n")
        f.write("3. 如果安装过程中遇到问题，您可能需要手动安装依赖关系\n")
    
    log_message(f"创建README文件: {readme_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="依赖包下载脚本")
    parser.add_argument(
        "--requirements", 
        default="requirements.txt", 
        help="指定requirements.txt文件路径"
    )
    parser.add_argument(
        "--output-dir", 
        default="offline_packages", 
        help="指定下载包的输出目录"
    )
    parser.add_argument(
        "--index-url", 
        help="指定pip镜像源URL"
    )
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
    
    # 解析requirements.txt
    packages = parse_requirements(args.requirements)
    if not packages:
        log_message("未找到有效的依赖包", "ERROR")
        sys.exit(1)
    
    log_message(f"从{args.requirements}解析出{len(packages)}个依赖包")
    
    # 从镜像URL提取主机名
    trusted_host = None
    if args.index_url:
        import re
        host_match = re.search(r"https?://([^/]+)", args.index_url)
        trusted_host = host_match.group(1) if host_match else None
    
    # 下载包
    succeeded, failed = download_packages(
        pip_command, 
        packages, 
        args.output_dir, 
        args.index_url, 
        trusted_host
    )
    
    # 创建离线安装脚本
    create_offline_install_script(args.output_dir)
    
    # 创建README
    create_readme(args.output_dir, succeeded, failed)
    
    # 输出结果摘要
    log_message(f"下载结果: 成功 {len(succeeded)}/{len(packages)}, 失败 {len(failed)}")
    if failed:
        log_message(f"以下包下载失败: {', '.join(failed)}", "WARNING")
    
    log_message(f"离线包已保存到目录: {os.path.abspath(args.output_dir)}")
    log_message(f"您可以将此目录传输到目标机器上，然后运行离线安装脚本")


if __name__ == "__main__":
    main() 