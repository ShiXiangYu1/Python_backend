#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目结构验证脚本

此脚本用于验证项目结构是否完整，检查必要的目录和文件是否存在，
以及配置文件是否一致。
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set


# 定义项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()


# 定义必要的目录
REQUIRED_DIRECTORIES = [
    "app",
    "app/api",
    "app/core",
    "app/db",
    "app/middlewares",
    "app/models",
    "app/schemas",
    "app/services",
    "app/tasks",
    "app/templates",
    "app/utils",
    "app/web",
    "alembic",
    "docs",
    "logs",
    "monitoring",
    "nginx",
    "scripts",
    "tests",
    "test_reports",
    "uploads",
]


# 定义必要的文件
REQUIRED_FILES = [
    "README.md",
    ".env.example",
    ".gitignore",
    "requirements.txt",
    "run.py",
    "alembic.ini",
    "app/main.py",
    "app/celery_app.py",
    "app/core/config.py",
    "app/core/celery.py",
    "app/core/security.py",
    "app/db/__init__.py",
    "app/models/__init__.py",
    "app/schemas/__init__.py",
    "app/services/__init__.py",
    "app/tasks/__init__.py",
]


# 定义需要README的目录
DIRECTORIES_NEED_README = [
    "scripts",
    "nginx",
    "monitoring",
    "uploads",
    "docs",
    "local_packages",
]


# 定义结果类别的颜色代码
class Colors:
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    RESET = "\033[0m"


def print_colored(message: str, color: str) -> None:
    """
    打印带颜色的消息

    参数:
        message: 要打印的消息
        color: 颜色代码
    """
    print(f"{color}{message}{Colors.RESET}")


def check_directory_exists(directory: str) -> bool:
    """
    检查目录是否存在

    参数:
        directory: 相对于项目根目录的目录路径

    返回:
        bool: 目录是否存在
    """
    dir_path = PROJECT_ROOT / directory
    return dir_path.exists() and dir_path.is_dir()


def check_file_exists(file_path: str) -> bool:
    """
    检查文件是否存在

    参数:
        file_path: 相对于项目根目录的文件路径

    返回:
        bool: 文件是否存在
    """
    full_path = PROJECT_ROOT / file_path
    return full_path.exists() and full_path.is_file()


def check_directory_has_readme(directory: str) -> bool:
    """
    检查目录是否有README.md文件

    参数:
        directory: 相对于项目根目录的目录路径

    返回:
        bool: 目录是否有README.md文件
    """
    readme_path = PROJECT_ROOT / directory / "README.md"
    return readme_path.exists() and readme_path.is_file()


def check_env_consistency() -> Tuple[bool, List[str]]:
    """
    检查.env和.env.example文件的一致性

    返回:
        Tuple[bool, List[str]]: 是否一致，不一致的项目列表
    """
    env_example_path = PROJECT_ROOT / ".env.example"
    env_path = PROJECT_ROOT / ".env"

    if not env_example_path.exists() or not env_path.exists():
        return False, ["缺少.env或.env.example文件"]

    env_example_vars = set()
    env_vars = set()

    # 读取.env.example中的变量
    with open(env_example_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                var_name = line.split("=", 1)[0].strip()
                env_example_vars.add(var_name)

    # 读取.env中的变量
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                var_name = line.split("=", 1)[0].strip()
                env_vars.add(var_name)

    # 查找不一致的变量
    missing_in_env = env_example_vars - env_vars
    extra_in_env = env_vars - env_example_vars

    inconsistencies = []
    if missing_in_env:
        inconsistencies.append(f".env缺少以下变量: {', '.join(missing_in_env)}")
    if extra_in_env:
        inconsistencies.append(f".env包含额外变量: {', '.join(extra_in_env)}")

    return len(inconsistencies) == 0, inconsistencies


def verify_project_structure() -> None:
    """
    验证项目结构并打印结果
    """
    print_colored("=== 项目结构验证 ===", Colors.GREEN)
    print()

    # 检查必要的目录
    print_colored("检查必要的目录:", Colors.GREEN)
    missing_dirs = []
    for directory in REQUIRED_DIRECTORIES:
        if check_directory_exists(directory):
            print(f"✅ {directory}")
        else:
            print_colored(f"❌ {directory} - 缺失", Colors.RED)
            missing_dirs.append(directory)
    print()

    # 检查必要的文件
    print_colored("检查必要的文件:", Colors.GREEN)
    missing_files = []
    for file_path in REQUIRED_FILES:
        if check_file_exists(file_path):
            print(f"✅ {file_path}")
        else:
            print_colored(f"❌ {file_path} - 缺失", Colors.RED)
            missing_files.append(file_path)
    print()

    # 检查目录README
    print_colored("检查目录README:", Colors.GREEN)
    missing_readmes = []
    for directory in DIRECTORIES_NEED_README:
        if check_directory_exists(directory):
            if check_directory_has_readme(directory):
                print(f"✅ {directory}/README.md")
            else:
                print_colored(f"❌ {directory}/README.md - 缺失", Colors.YELLOW)
                missing_readmes.append(directory)
    print()

    # 检查环境变量一致性
    print_colored("检查环境变量一致性:", Colors.GREEN)
    is_consistent, inconsistencies = check_env_consistency()
    if is_consistent:
        print("✅ .env和.env.example一致")
    else:
        print_colored("❌ .env和.env.example不一致:", Colors.YELLOW)
        for inconsistency in inconsistencies:
            print_colored(f"  - {inconsistency}", Colors.YELLOW)
    print()

    # 输出总结
    print_colored("=== 验证结果总结 ===", Colors.GREEN)
    print()

    if not missing_dirs and not missing_files:
        print_colored("✅ 所有必要的目录和文件都存在!", Colors.GREEN)
    else:
        if missing_dirs:
            print_colored(f"❌ 缺少{len(missing_dirs)}个必要目录", Colors.RED)
        if missing_files:
            print_colored(f"❌ 缺少{len(missing_files)}个必要文件", Colors.RED)

    if missing_readmes:
        print_colored(f"⚠️ {len(missing_readmes)}个目录缺少README文件", Colors.YELLOW)

    if not is_consistent:
        print_colored("⚠️ 环境变量配置不一致", Colors.YELLOW)

    print()
    total_checks = len(REQUIRED_DIRECTORIES) + len(REQUIRED_FILES) + len(DIRECTORIES_NEED_README) + 1
    passed_checks = (
        len(REQUIRED_DIRECTORIES) - len(missing_dirs)
        + len(REQUIRED_FILES) - len(missing_files)
        + len(DIRECTORIES_NEED_README) - len(missing_readmes)
        + (1 if is_consistent else 0)
    )
    pass_rate = (passed_checks / total_checks) * 100

    print_colored(f"总体完成度: {pass_rate:.2f}% ({passed_checks}/{total_checks})", Colors.GREEN)
    
    # 提供建议
    if missing_dirs or missing_files or missing_readmes or not is_consistent:
        print()
        print_colored("=== 建议 ===", Colors.GREEN)
        
        if missing_dirs:
            print_colored("1. 创建缺失的目录:", Colors.YELLOW)
            for directory in missing_dirs:
                print(f"   mkdir -p {directory}")
        
        if missing_files:
            print_colored("2. 创建缺失的文件:", Colors.YELLOW)
            for file_path in missing_files:
                print(f"   touch {file_path}")
        
        if missing_readmes:
            print_colored("3. 为以下目录添加README.md文件:", Colors.YELLOW)
            for directory in missing_readmes:
                print(f"   touch {directory}/README.md")
        
        if not is_consistent:
            print_colored("4. 更新环境变量配置，确保.env和.env.example一致", Colors.YELLOW)


if __name__ == "__main__":
    verify_project_structure() 