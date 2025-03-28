#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
综合功能测试脚本

测试AI模型平台的主要功能，包括用户认证、模型管理、API密钥管理和系统监控。
验证各个组件是否能够正常协同工作。
"""

import os
import sys
import json
import time
import logging
import asyncio
import tempfile
import socket
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("集成测试")

# 依赖检查
def check_dependencies():
    """检查必要的依赖是否已安装"""
    dependencies = [
        ("httpx", "HTTP客户端，用于API测试"),
        ("pytest", "测试框架"),
        ("fastapi", "FastAPI框架"),
        ("sqlalchemy", "数据库ORM"),
        ("pydantic", "数据验证")
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
        sys.exit(1)

# 检查服务是否可用
def is_service_running(host="localhost", port=8000):
    """检查服务是否正在运行"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 测试用户信息
TEST_USER = {
    "username": "test_integration",
    "email": "test_integration@example.com",
    "password": "testpassword123",
    "confirm_password": "testpassword123",
    "full_name": "测试集成用户"
}

# 测试管理员信息
ADMIN_USER = {
    "username": "admin",
    "password": "admin123"
}

# 测试模型信息
TEST_MODEL = {
    "name": "测试模型",
    "description": "用于集成测试的模型",
    "framework": "pytorch",
    "version": "1.0.0",
    "is_public": True
}

# 测试API密钥信息
TEST_API_KEY = {
    "name": "测试API密钥",
    "scopes": "models:read,models:write",
    "expires_at": None
}


class IntegrationTest:
    """集成测试类"""
    
    def __init__(self):
        """初始化测试客户端和状态"""
        try:
            import httpx
            self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        except ImportError:
            logger.error("未安装httpx库，无法进行测试")
            sys.exit(1)
            
        self.access_token = None
        self.user_id = None
        self.model_id = None
        self.api_key_id = None
        self.api_key = None
        self.test_file_path = None
    
    async def close(self):
        """关闭测试客户端"""
        await self.client.aclose()
    
    async def login(self, username: str, password: str) -> bool:
        """
        用户登录
        
        参数:
            username: 用户名
            password: 密码
            
        返回:
            bool: 登录是否成功
        """
        try:
            response = await self.client.post(
                "/auth/login/json",
                json={"username": username, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.client.headers["Authorization"] = f"Bearer {self.access_token}"
                logger.info(f"用户 {username} 登录成功")
                return True
            else:
                logger.error(f"登录失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"登录时发生错误: {str(e)}")
            return False
    
    async def register(self, user_data: Dict[str, Any]) -> bool:
        """
        注册用户
        
        参数:
            user_data: 用户数据
            
        返回:
            bool: 注册是否成功
        """
        try:
            response = await self.client.post("/auth/register", json=user_data)
            if response.status_code == 200:
                data = response.json()
                self.user_id = data["id"]
                logger.info(f"用户注册成功，ID: {self.user_id}")
                return True
            elif response.status_code == 400 and "already exists" in response.text:
                logger.warning("用户已存在，尝试直接登录")
                return await self.login(user_data["username"], user_data["password"])
            else:
                logger.error(f"注册失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"注册时发生错误: {str(e)}")
            return False
    
    async def create_model(self, model_data: Dict[str, Any]) -> bool:
        """
        创建模型
        
        参数:
            model_data: 模型数据
            
        返回:
            bool: 创建是否成功
        """
        try:
            response = await self.client.post("/models", json=model_data)
            if response.status_code == 200:
                data = response.json()
                self.model_id = data["id"]
                logger.info(f"模型创建成功，ID: {self.model_id}")
                return True
            else:
                logger.error(f"创建模型失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"创建模型时发生错误: {str(e)}")
            return False
    
    async def create_test_file(self) -> bool:
        """
        创建测试模型文件
        
        返回:
            bool: 创建是否成功
        """
        try:
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pt")
            temp_file.write(b"This is a test model file")
            temp_file.close()
            self.test_file_path = temp_file.name
            logger.info(f"创建测试文件成功: {self.test_file_path}")
            return True
        except Exception as e:
            logger.error(f"创建测试文件时发生错误: {str(e)}")
            return False
    
    async def upload_model_file(self) -> bool:
        """
        上传模型文件
        
        返回:
            bool: 上传是否成功
        """
        if not self.model_id or not self.test_file_path:
            logger.error("缺少模型ID或测试文件路径")
            return False
        
        try:
            with open(self.test_file_path, "rb") as f:
                files = {"file": (os.path.basename(self.test_file_path), f, "application/octet-stream")}
                response = await self.client.post(
                    f"/models/{self.model_id}/upload",
                    files=files
                )
            
            if response.status_code == 200:
                logger.info("模型文件上传成功")
                return True
            else:
                logger.error(f"上传模型文件失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"上传模型文件时发生错误: {str(e)}")
            return False
        finally:
            # 清理测试文件
            if self.test_file_path and os.path.exists(self.test_file_path):
                os.unlink(self.test_file_path)
                self.test_file_path = None
    
    async def deploy_model(self) -> bool:
        """
        部署模型
        
        返回:
            bool: 部署是否成功
        """
        if not self.model_id:
            logger.error("缺少模型ID")
            return False
        
        try:
            response = await self.client.post(f"/models/{self.model_id}/deploy")
            if response.status_code == 200:
                logger.info("模型部署成功")
                return True
            else:
                logger.error(f"部署模型失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"部署模型时发生错误: {str(e)}")
            return False
    
    async def create_api_key(self, api_key_data: Dict[str, Any]) -> bool:
        """
        创建API密钥
        
        参数:
            api_key_data: API密钥数据
            
        返回:
            bool: 创建是否成功
        """
        try:
            response = await self.client.post("/api-keys", json=api_key_data)
            if response.status_code == 200:
                data = response.json()
                self.api_key_id = data["id"]
                self.api_key = data["key"]
                logger.info(f"API密钥创建成功，ID: {self.api_key_id}")
                return True
            else:
                logger.error(f"创建API密钥失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"创建API密钥时发生错误: {str(e)}")
            return False
    
    async def test_api_key_auth(self) -> bool:
        """
        测试API密钥认证
        
        返回:
            bool: 测试是否成功
        """
        if not self.api_key:
            logger.error("缺少API密钥")
            return False
        
        try:
            # 创建一个新的无认证的客户端
            import httpx
            temp_client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
            temp_client.headers["X-API-Key"] = self.api_key
            
            # 尝试获取用户信息
            response = await temp_client.get("/users/me")
            await temp_client.aclose()
            
            if response.status_code == 200:
                data = response.json()
                if data["id"] == self.user_id:
                    logger.info("API密钥认证成功")
                    return True
                else:
                    logger.error("API密钥认证返回了错误的用户信息")
                    return False
            else:
                logger.error(f"API密钥认证失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"测试API密钥认证时发生错误: {str(e)}")
            return False
    
    async def check_prometheus_metrics(self) -> bool:
        """
        检查Prometheus指标端点
        
        返回:
            bool: 检查是否成功
        """
        try:
            # 访问指标端点
            response = await self.client.get("/metrics")
            if response.status_code == 200:
                metrics_text = response.text
                # 检查一些关键指标是否存在
                required_metrics = [
                    "http_requests_total", 
                    "http_request_duration_seconds",
                    "model_operations_total"
                ]
                for metric in required_metrics:
                    if metric not in metrics_text:
                        logger.error(f"指标 {metric} 未找到")
                        return False
                
                logger.info("Prometheus指标检查成功")
                return True
            else:
                logger.error(f"访问指标端点失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"检查Prometheus指标时发生错误: {str(e)}")
            return False
    
    async def check_health(self) -> bool:
        """
        检查健康状态端点
        
        返回:
            bool: 检查是否成功
        """
        try:
            response = await self.client.get("/health")
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "healthy" and data["database"] == "connected":
                    logger.info("健康检查成功")
                    return True
                else:
                    logger.error(f"健康状态异常: {data}")
                    return False
            else:
                logger.error(f"健康检查失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"健康检查时发生错误: {str(e)}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """
        运行所有测试
        
        返回:
            Dict[str, bool]: 各个测试的结果
        """
        results = {}
        
        # 检查健康状态
        results["健康检查"] = await self.check_health()
        
        # 用户认证测试
        results["用户注册"] = await self.register(TEST_USER)
        results["用户登录"] = await self.login(TEST_USER["username"], TEST_USER["password"])
        
        if results["用户登录"]:
            # 模型管理测试
            results["创建模型"] = await self.create_model(TEST_MODEL)
            if results["创建模型"]:
                results["创建测试文件"] = await self.create_test_file()
                if results["创建测试文件"]:
                    results["上传模型文件"] = await self.upload_model_file()
                    if results["上传模型文件"]:
                        results["部署模型"] = await self.deploy_model()
            
            # API密钥测试
            results["创建API密钥"] = await self.create_api_key(TEST_API_KEY)
            if results["创建API密钥"]:
                results["API密钥认证"] = await self.test_api_key_auth()
            
            # 监控系统测试
            results["Prometheus指标"] = await self.check_prometheus_metrics()
        
        return results


async def main():
    """主函数"""
    # 检查依赖
    check_dependencies()
    
    # 检查服务可用性
    if not is_service_running():
        logger.error("API服务不可用，请确保服务器正在运行并监听8000端口")
        logger.info("可以使用以下命令启动服务：uvicorn app.main:app --reload")
        sys.exit(1)
    
    tester = IntegrationTest()
    try:
        # 运行所有测试
        results = await tester.run_all_tests()
        
        # 打印测试结果
        logger.info("\n" + "="*50)
        logger.info("集成测试结果:")
        logger.info("="*50)
        
        all_passed = True
        for test_name, passed in results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            logger.info(f"{test_name}: {status}")
            if not passed:
                all_passed = False
        
        logger.info("="*50)
        if all_passed:
            logger.info("🎉 所有测试通过！系统功能正常整合。")
            return 0
        else:
            logger.error("❗ 部分测试失败，请检查系统配置和日志。")
            return 1
    except Exception as e:
        logger.critical(f"测试过程中发生严重错误: {str(e)}")
        return 1
    finally:
        await tester.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 