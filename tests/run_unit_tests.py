#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
单元测试运行脚本

提供一个简单的方式来运行项目的单元测试，支持选择性测试和详细输出。
"""

import os
import sys
import argparse
import pytest


def run_unit_tests(test_path=None, verbose=False, fail_fast=False):
    """
    运行单元测试
    
    参数:
        test_path: 测试路径，可以是文件或目录
        verbose: 是否显示详细输出
        fail_fast: 是否在第一个测试失败时停止
        
    返回:
        int: 测试结果代码（0表示成功）
    """
    # 设置测试参数
    args = []
    
    # 设置测试路径
    if test_path:
        args.append(test_path)
    else:
        args.append("tests/unit")
    
    # 设置详细输出
    if verbose:
        args.append("-v")
    
    # 设置失败快速
    if fail_fast:
        args.append("-x")
    
    # 添加颜色输出
    args.append("--color=yes")
    
    # 运行测试
    return pytest.main(args)


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="运行项目单元测试")
    parser.add_argument(
        "path", 
        nargs="?", 
        help="要测试的路径（文件或目录）"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="显示详细输出"
    )
    parser.add_argument(
        "-x", "--fail-fast", 
        action="store_true", 
        help="在第一个测试失败时停止"
    )
    
    args = parser.parse_args()
    
    # 运行测试
    result = run_unit_tests(
        test_path=args.path,
        verbose=args.verbose,
        fail_fast=args.fail_fast
    )
    
    # 退出
    sys.exit(result) 