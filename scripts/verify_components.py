#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
组件验证脚本

验证系统各个核心组件是否能正常加载和运行。
这是一个轻量级测试，不需要运行完整的服务器。
"""

import os
import sys
import importlib.util
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("组件验证")

# 路径设置
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

def check_dependencies():
    """检查必要的依赖是否已安装"""
    dependencies = [
        ("fastapi", "FastAPI框架"),
        ("sqlalchemy", "数据库ORM"),
        ("pydantic", "数据验证"),
        ("alembic", "数据库迁移工具"),
        ("uvicorn", "ASGI服务器")
    ]
    
    missing_deps = []
    for dep, desc in dependencies:
        if importlib.util.find_spec(dep) is None:
            missing_deps.append((dep, desc))
    
    if missing_deps:
        logger.error("以下依赖缺失，请先安装：")
        for dep, desc in missing_deps:
            logger.error(f"  - {dep}: {desc}")
        logger.info("可以使用以下命令安装依赖：pip install -r requirements.txt")
        return False
    return True

def check_config_module():
    """检查配置模块是否存在和加载正常"""
    try:
        from app.core.config import settings
        logger.info(f"配置模块加载成功，应用名称：{settings.APP_NAME}")
        return True
    except ImportError as e:
        logger.error(f"配置模块导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"配置模块加载失败: {e}")
        return False

def check_database_module():
    """检查数据库模块是否存在和配置正确"""
    try:
        from app.db.session import engine, get_db
        logger.info("数据库会话模块加载成功")
        
        # 检查数据库文件是否存在（SQLite）
        if 'sqlite' in str(engine.url):
            db_path = str(engine.url).replace('sqlite:///', '')
            if os.path.exists(db_path):
                logger.info(f"SQLite数据库文件已存在: {db_path}")
            else:
                logger.warning(f"SQLite数据库文件不存在: {db_path}")
        else:
            logger.info(f"使用非SQLite数据库: {engine.url}")
        
        return True
    except ImportError as e:
        logger.error(f"数据库模块导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"数据库模块加载失败: {e}")
        return False

def check_models():
    """检查模型类是否存在和定义正确"""
    try:
        from app.models.user import User, UserRole
        from app.models.api_key import APIKey
        from app.models.model import Model, ModelVersion, ModelStatus
        
        logger.info("数据模型加载成功")
        logger.info(f"用户角色: {[role.value for role in UserRole]}")
        return True
    except ImportError as e:
        logger.error(f"模型类导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"模型类加载失败: {e}")
        return False

def check_env_file():
    """检查环境变量文件是否存在"""
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        logger.info(f".env文件已存在: {env_file}")
        return True
    else:
        logger.warning(f".env文件不存在: {env_file}")
        logger.info("您可能需要从.env.example创建.env文件")
        return False

def check_database_file():
    """检查SQLite数据库文件是否存在"""
    db_file = BASE_DIR / 'app.db'
    if db_file.exists():
        logger.info(f"数据库文件已存在: {db_file}")
        file_size = db_file.stat().st_size
        logger.info(f"数据库文件大小: {file_size} 字节")
        return True
    else:
        logger.warning(f"数据库文件不存在: {db_file}")
        logger.info("您可能需要运行迁移脚本: alembic upgrade head")
        return False

def check_app_loading():
    """检查主应用是否能正常加载"""
    try:
        from app.main import app
        logger.info(f"主应用加载成功，标题：{app.title}")
        
        # 检查API路由
        routes = [
            {"path": route.path, "name": route.name, "methods": route.methods}
            for route in app.routes
        ]
        
        # 打印部分路由信息
        if routes:
            logger.info(f"加载了 {len(routes)} 个路由")
            for i, route in enumerate(routes[:5]):
                logger.info(f"路由 {i+1}: {route['path']} [{','.join(route['methods'])}]")
            if len(routes) > 5:
                logger.info(f"... 等 {len(routes)-5} 个其他路由")
        else:
            logger.warning("没有找到任何路由")
        
        return True
    except ImportError as e:
        logger.error(f"主应用导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"主应用加载失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始验证系统组件...")
    
    # 检查项目结构
    if not os.path.isdir(os.path.join(BASE_DIR, 'app')):
        logger.error(f"项目结构错误：无法找到app目录，当前目录：{BASE_DIR}")
        return 1
    
    # 检查文件和目录
    app_dirs = [d for d in os.listdir(os.path.join(BASE_DIR, 'app')) 
                if os.path.isdir(os.path.join(BASE_DIR, 'app', d))]
    logger.info(f"app目录结构: {', '.join(app_dirs)}")
    
    # 运行验证
    results = {
        "依赖检查": check_dependencies(),
        "环境文件": check_env_file(),
        "配置模块": check_config_module(),
        "数据库文件": check_database_file(),
        "数据库模块": check_database_module(),
        "数据模型": check_models(),
        "主应用加载": check_app_loading()
    }
    
    # 打印结果
    logger.info("\n" + "="*50)
    logger.info("组件验证结果:")
    logger.info("="*50)
    
    all_passed = True
    for check_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{check_name}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("="*50)
    if all_passed:
        logger.info("🎉 所有组件验证通过！系统结构完整。")
        return 0
    else:
        logger.error("❗ 部分组件验证失败，请参考上述日志解决问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 