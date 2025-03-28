#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化版集成测试

该脚本执行基本的组件测试，不需要完整的依赖环境，
主要验证以下内容：
1. 文件结构是否完整
2. 配置文件是否正确
3. API设计是否合理
4. 模块划分是否清晰
"""

import os
import sys
import json
import logging
from pathlib import Path
import inspect
import time
import datetime
from typing import List, Dict, Any

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("简化集成测试")

# 路径设置
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

class FileStructureValidator:
    """文件结构验证器"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.required_dirs = [
            'app',
            'app/api',
            'app/core',
            'app/db',
            'app/models',
            'app/schemas',
            'app/services',
            'app/web',
            'tests',
        ]
        self.required_files = [
            'app/main.py',
            'app/core/config.py',
            'app/db/session.py',
            'app/models/user.py',
            'app/models/api_key.py',
            'app/models/model.py',
            'requirements.txt',
            '.env',
        ]
    
    def validate(self) -> Dict[str, Any]:
        """验证文件结构"""
        result = {
            "missing_dirs": [],
            "missing_files": [],
            "found_dirs": [],
            "found_files": [],
            "all_passed": True
        }
        
        # 检查目录
        for dir_path in self.required_dirs:
            full_path = self.base_dir / dir_path
            if full_path.exists() and full_path.is_dir():
                result["found_dirs"].append(dir_path)
            else:
                result["missing_dirs"].append(dir_path)
                result["all_passed"] = False
        
        # 检查文件
        for file_path in self.required_files:
            full_path = self.base_dir / file_path
            if full_path.exists() and full_path.is_file():
                result["found_files"].append(file_path)
            else:
                result["missing_files"].append(file_path)
                result["all_passed"] = False
        
        return result

class ApiDefinitionAnalyzer:
    """API定义分析器"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.api_dir = base_dir / 'app' / 'api'
        self.router_files = []
    
    def analyze(self) -> Dict[str, Any]:
        """分析API定义"""
        result = {
            "router_files": [],
            "endpoints": [],
            "has_basic_endpoints": False
        }
        
        # 检查API路由文件
        if not self.api_dir.exists():
            return result
        
        # 收集所有路由文件
        for file in self.api_dir.glob('**/*.py'):
            if file.name.startswith('_'):
                continue
            
            relative_path = file.relative_to(self.base_dir)
            result["router_files"].append(str(relative_path))
            
            # 分析文件内容
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 简单解析路由定义
                endpoints = []
                for line in content.split('\n'):
                    # 检测API端点定义
                    if '@router.' in line and ('get(' in line or 'post(' in line or 
                                           'put(' in line or 'delete(' in line):
                        endpoints.append(line.strip())
                
                if endpoints:
                    result["endpoints"].extend(endpoints)
        
        # 判断是否具有基本的端点（用户、模型、API密钥）
        essential_keywords = ['user', 'model', 'api_key', 'health']
        for keyword in essential_keywords:
            if any(keyword in endpoint.lower() for endpoint in result["endpoints"]):
                result["has_basic_endpoints"] = True
                break
        
        return result

class ModelSchemaValidator:
    """模型和Schema验证器"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.models_dir = base_dir / 'app' / 'models'
        self.schemas_dir = base_dir / 'app' / 'schemas'
    
    def validate(self) -> Dict[str, Any]:
        """验证模型和Schema定义"""
        result = {
            "models": [],
            "schemas": [],
            "has_essential_models": False,
            "has_corresponding_schemas": False,
        }
        
        # 检查模型文件
        if self.models_dir.exists():
            for file in self.models_dir.glob('*.py'):
                if file.name.startswith('_'):
                    continue
                
                model_name = file.stem
                result["models"].append(model_name)
        
        # 检查Schema文件
        if self.schemas_dir.exists():
            for file in self.schemas_dir.glob('*.py'):
                if file.name.startswith('_'):
                    continue
                
                schema_name = file.stem
                result["schemas"].append(schema_name)
        
        # 检查是否有基本模型
        essential_models = ['user', 'model', 'api_key']
        if all(model in result["models"] for model in essential_models):
            result["has_essential_models"] = True
        
        # 检查模型是否有对应的Schema
        if result["models"] and result["schemas"]:
            # 检查是否有相同名称的模型和Schema
            common_names = set(result["models"]).intersection(set(result["schemas"]))
            if len(common_names) >= 3:  # 至少3个模型有对应Schema
                result["has_corresponding_schemas"] = True
        
        return result

class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.config_file = base_dir / 'app' / 'core' / 'config.py'
        self.env_file = base_dir / '.env'
    
    def validate(self) -> Dict[str, Any]:
        """验证配置文件"""
        result = {
            "config_exists": self.config_file.exists(),
            "env_exists": self.env_file.exists(),
            "required_settings": [],
            "missing_settings": [],
            "all_passed": False
        }
        
        # 基本必需的配置项
        required_settings = [
            'SECRET_KEY', 
            'ALGORITHM', 
            'ACCESS_TOKEN_EXPIRE_MINUTES',
            'DATABASE_URL',
            'APP_NAME'
        ]
        
        # 检查环境变量文件
        if result["env_exists"]:
            env_vars = {}
            try:
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
                
                # 检查必需的配置项
                for setting in required_settings:
                    if setting in env_vars:
                        result["required_settings"].append(setting)
                    else:
                        result["missing_settings"].append(setting)
                
                if not result["missing_settings"]:
                    result["all_passed"] = True
            except Exception as e:
                logger.error(f"无法解析.env文件: {e}")
        
        return result

class ServiceLayerAnalyzer:
    """服务层分析器"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.services_dir = base_dir / 'app' / 'services'
    
    def analyze(self) -> Dict[str, Any]:
        """分析服务层实现"""
        result = {
            "service_files": [],
            "has_service_layer": False,
            "has_essential_services": False
        }
        
        # 检查服务目录是否存在
        if not self.services_dir.exists():
            return result
        
        result["has_service_layer"] = True
        
        # 收集所有服务文件
        for file in self.services_dir.glob('*.py'):
            if file.name.startswith('_'):
                continue
            
            service_name = file.stem
            result["service_files"].append(service_name)
        
        # 检查是否具有基本服务
        essential_services = ['user', 'model', 'api_key']
        matches = sum(1 for service in result["service_files"] 
                     if any(ess in service.lower() for ess in essential_services))
        
        if matches >= 2:  # 至少有2个基本服务
            result["has_essential_services"] = True
        
        return result

class TestSuiteAnalyzer:
    """测试套件分析器"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.tests_dir = base_dir / 'tests'
    
    def analyze(self) -> Dict[str, Any]:
        """分析测试套件"""
        result = {
            "test_files": [],
            "has_tests": False,
            "has_api_tests": False,
            "has_unit_tests": False
        }
        
        # 检查测试目录是否存在
        if not self.tests_dir.exists():
            return result
        
        result["has_tests"] = True
        
        # 收集所有测试文件
        for file in self.tests_dir.glob('**/*.py'):
            if file.name.startswith('_'):
                continue
            
            relative_path = file.relative_to(self.base_dir)
            result["test_files"].append(str(relative_path))
            
            # 检查是否有API测试
            if 'api' in str(file) and not result["has_api_tests"]:
                result["has_api_tests"] = True
            
            # 检查是否有单元测试
            if ('unit' in str(file) or 'service' in str(file)) and not result["has_unit_tests"]:
                result["has_unit_tests"] = True
        
        return result

def run_integration_test():
    """运行集成测试"""
    logger.info("开始运行简化版集成测试...")
    start_time = time.time()
    
    results = {}
    
    # 文件结构验证
    logger.info("1. 验证文件结构...")
    file_validator = FileStructureValidator(BASE_DIR)
    results["file_structure"] = file_validator.validate()
    
    # API定义分析
    logger.info("2. 分析API定义...")
    api_analyzer = ApiDefinitionAnalyzer(BASE_DIR)
    results["api_definition"] = api_analyzer.analyze()
    
    # 模型和Schema验证
    logger.info("3. 验证模型和Schema...")
    model_validator = ModelSchemaValidator(BASE_DIR)
    results["model_schema"] = model_validator.validate()
    
    # 配置验证
    logger.info("4. 验证配置文件...")
    config_validator = ConfigValidator(BASE_DIR)
    results["config"] = config_validator.validate()
    
    # 服务层分析
    logger.info("5. 分析服务层实现...")
    service_analyzer = ServiceLayerAnalyzer(BASE_DIR)
    results["service_layer"] = service_analyzer.analyze()
    
    # 测试套件分析
    logger.info("6. 分析测试套件...")
    test_analyzer = TestSuiteAnalyzer(BASE_DIR)
    results["test_suite"] = test_analyzer.analyze()
    
    # 计算总体评分
    score = 0
    max_score = 6
    
    if results["file_structure"]["all_passed"]:
        score += 1
    
    if results["api_definition"]["has_basic_endpoints"]:
        score += 1
        
    if results["model_schema"]["has_essential_models"] and results["model_schema"]["has_corresponding_schemas"]:
        score += 1
    
    if results["config"]["all_passed"]:
        score += 1
    
    if results["service_layer"]["has_essential_services"]:
        score += 1
    
    if results["test_suite"]["has_api_tests"] and results["test_suite"]["has_unit_tests"]:
        score += 1
    
    # 生成测试报告
    report = {
        "test_time": datetime.datetime.now().isoformat(),
        "duration": time.time() - start_time,
        "overall_score": f"{score}/{max_score}",
        "passed_percentage": round(score / max_score * 100, 2),
        "results": results
    }
    
    return report

def print_report(report):
    """打印测试报告"""
    logger.info("\n" + "="*60)
    logger.info("简化版集成测试报告")
    logger.info("="*60)
    
    logger.info(f"测试时间: {report['test_time']}")
    logger.info(f"耗时: {report['duration']:.2f}秒")
    logger.info(f"总体评分: {report['overall_score']} ({report['passed_percentage']}%)")
    logger.info("-"*60)
    
    # 文件结构
    structure = report["results"]["file_structure"]
    logger.info("1. 文件结构验证:")
    status = "✅ 通过" if structure["all_passed"] else "❌ 失败"
    logger.info(f"   状态: {status}")
    if structure["missing_dirs"]:
        logger.warning(f"   缺少目录: {', '.join(structure['missing_dirs'])}")
    if structure["missing_files"]:
        logger.warning(f"   缺少文件: {', '.join(structure['missing_files'])}")
    
    # API定义
    api = report["results"]["api_definition"]
    logger.info("2. API定义分析:")
    status = "✅ 通过" if api["has_basic_endpoints"] else "❌ 失败"
    logger.info(f"   状态: {status}")
    logger.info(f"   发现路由文件: {len(api['router_files'])}")
    logger.info(f"   发现端点: {len(api['endpoints'])}")
    
    # 模型和Schema
    model = report["results"]["model_schema"]
    logger.info("3. 模型和Schema验证:")
    status = "✅ 通过" if model["has_essential_models"] and model["has_corresponding_schemas"] else "❌ 失败"
    logger.info(f"   状态: {status}")
    logger.info(f"   模型: {', '.join(model['models'])}")
    logger.info(f"   Schemas: {', '.join(model['schemas'])}")
    
    # 配置验证
    config = report["results"]["config"]
    logger.info("4. 配置验证:")
    status = "✅ 通过" if config["all_passed"] else "❌ 失败"
    logger.info(f"   状态: {status}")
    if config["missing_settings"]:
        logger.warning(f"   缺少配置项: {', '.join(config['missing_settings'])}")
    
    # 服务层分析
    service = report["results"]["service_layer"]
    logger.info("5. 服务层分析:")
    status = "✅ 通过" if service["has_essential_services"] else "❌ 失败"
    logger.info(f"   状态: {status}")
    logger.info(f"   服务文件: {', '.join(service['service_files'])}")
    
    # 测试套件分析
    test = report["results"]["test_suite"]
    logger.info("6. 测试套件分析:")
    status = "✅ 通过" if test["has_api_tests"] and test["has_unit_tests"] else "❌ 失败"
    logger.info(f"   状态: {status}")
    logger.info(f"   测试文件数量: {len(test['test_files'])}")
    logger.info(f"   API测试: {'是' if test['has_api_tests'] else '否'}")
    logger.info(f"   单元测试: {'是' if test['has_unit_tests'] else '否'}")
    
    # 总结
    logger.info("-"*60)
    if report["passed_percentage"] >= 80:
        logger.info("🎉 总体评价: 优秀！该项目结构完整，符合最佳实践。")
    elif report["passed_percentage"] >= 60:
        logger.info("👍 总体评价: 良好。该项目基本符合要求，但有改进空间。")
    else:
        logger.info("⚠️ 总体评价: 需要改进。该项目存在一些问题，请参考上述报告进行修复。")
    
    logger.info("="*60)

def main():
    """主函数"""
    try:
        report = run_integration_test()
        print_report(report)
        
        # 将报告保存为JSON文件
        report_file = BASE_DIR / 'integration_test_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试报告已保存至: {report_file}")
        
        return 0 if report["passed_percentage"] >= 60 else 1
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main()) 