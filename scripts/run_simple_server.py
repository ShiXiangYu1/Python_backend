#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化版服务器启动脚本

此脚本用于启动简化版的API服务器，不依赖第三方库，仅使用Python标准库。
"""

import os
import sys
import importlib.util

def import_simplified_main():
    """导入简化版主模块"""
    try:
        # 尝试导入简化版主模块
        spec = importlib.util.spec_from_file_location(
            "simplified_main",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                        "app", "simplified_main.py")
        )
        simplified_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(simplified_main)
        return simplified_main
    except Exception as e:
        print(f"错误: 无法导入简化版主模块: {e}")
        sys.exit(1)

def main():
    """主函数，启动简化版服务器"""
    print("="*50)
    print("启动简化版API服务器")
    print("此服务器使用Python标准库实现，不依赖FastAPI等第三方库")
    print("="*50)
    
    # 检查Python版本
    if sys.version_info < (3, 6):
        print("错误: 需要Python 3.6或更高版本")
        sys.exit(1)
    
    # 导入简化版主模块
    simplified_main = import_simplified_main()
    
    # 运行服务器
    try:
        simplified_main.run_server()
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动服务器时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 