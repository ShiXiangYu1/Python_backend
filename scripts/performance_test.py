#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
性能测试脚本

该脚本对系统API进行性能测试，评估响应时间和吞吐量。
不需要完整的依赖环境，可以在任何环境中执行。
"""

import asyncio
import time
import json
import logging
import argparse
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("性能测试")

# 默认设置
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8000
DEFAULT_CONCURRENCY = 5
DEFAULT_REQUESTS = 100
DEFAULT_TIMEOUT = 10
DEFAULT_AUTH = None  # 可以是Bearer token或API key
DEFAULT_OUTPUT = "./performance_results.json"

class APIPerformanceTester:
    """API性能测试器"""
    
    def __init__(
        self, 
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        concurrency: int = DEFAULT_CONCURRENCY,
        requests_count: int = DEFAULT_REQUESTS,
        timeout: int = DEFAULT_TIMEOUT,
        auth_token: Optional[str] = DEFAULT_AUTH,
        output_file: str = DEFAULT_OUTPUT
    ):
        """初始化性能测试器
        
        参数:
            host: API主机名
            port: API端口
            concurrency: 并发请求数
            requests_count: 总请求数
            timeout: 请求超时时间（秒）
            auth_token: 授权令牌（可选）
            output_file: 结果输出文件
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.concurrency = concurrency
        self.requests_count = requests_count
        self.timeout = timeout
        self.auth_token = auth_token
        self.output_file = output_file
        self.results = {}
        
        # 确保输出目录存在
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def _make_request(self, session, endpoint: str, method: str = "GET", data: Any = None) -> Dict[str, Any]:
        """发送单个请求
        
        参数:
            session: HTTPX会话
            endpoint: API端点
            method: HTTP方法
            data: 请求数据
            
        返回:
            字典，包含响应结果和性能数据
        """
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.auth_token:
            if self.auth_token.startswith("Bearer "):
                headers["Authorization"] = self.auth_token
            else:
                headers["X-API-Key"] = self.auth_token
                
        try:
            # 我们将使用标准库，而不是httpx，以避免依赖问题
            import urllib.request
            import urllib.error
            import ssl
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            start_time = time.time()
            
            if method == "GET":
                req = urllib.request.Request(url, headers=headers)
                try:
                    with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as response:
                        status_code = response.status
                        content = response.read().decode('utf-8')
                except urllib.error.HTTPError as e:
                    status_code = e.code
                    content = e.read().decode('utf-8')
            else:  # POST, PUT, DELETE
                data_bytes = json.dumps(data).encode('utf-8') if data else None
                req = urllib.request.Request(
                    url, 
                    data=data_bytes,
                    headers={**headers, 'Content-Type': 'application/json'},
                    method=method
                )
                try:
                    with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as response:
                        status_code = response.status
                        content = response.read().decode('utf-8')
                except urllib.error.HTTPError as e:
                    status_code = e.code
                    content = e.read().decode('utf-8')
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 毫秒
            
            return {
                "status_code": status_code,
                "response_time": response_time,
                "success": 200 <= status_code < 300,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 毫秒
            
            return {
                "status_code": 0,
                "response_time": response_time,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _run_test_for_endpoint(self, endpoint: str, method: str = "GET", data: Any = None, session = None) -> Dict[str, Any]:
        """对单个端点运行测试
        
        参数:
            endpoint: API端点
            method: HTTP方法
            data: 请求数据
            session: HTTPX会话
            
        返回:
            字典，包含测试结果
        """
        tasks = []
        for _ in range(self.requests_count):
            tasks.append(self._make_request(session, endpoint, method, data))
        
        logger.info(f"对端点 {endpoint} 开始 {self.requests_count} 个请求（{method}）...")
        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        total_time = end_time - start_time
        
        # 处理结果
        successful_responses = [r for r in responses if isinstance(r, dict) and r.get('success', False)]
        failed_responses = [r for r in responses if isinstance(r, dict) and not r.get('success', False)]
        error_responses = [r for r in responses if not isinstance(r, dict)]
        
        if successful_responses:
            response_times = [r['response_time'] for r in successful_responses]
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            med_response_time = statistics.median(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0
            
            requests_per_second = len(successful_responses) / total_time
        else:
            avg_response_time = 0
            min_response_time = 0
            max_response_time = 0
            med_response_time = 0
            p95_response_time = 0
            requests_per_second = 0
        
        result = {
            "endpoint": endpoint,
            "method": method,
            "total_requests": self.requests_count,
            "successful_requests": len(successful_responses),
            "failed_requests": len(failed_responses),
            "error_requests": len(error_responses),
            "total_time": total_time,
            "avg_response_time": avg_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "median_response_time": med_response_time,
            "p95_response_time": p95_response_time,
            "requests_per_second": requests_per_second
        }
        
        logger.info(f"端点 {endpoint} 测试完成: {len(successful_responses)}/{self.requests_count} 成功, "
                   f"平均响应时间: {avg_response_time:.2f}ms, RPS: {requests_per_second:.2f}")
        
        return result
    
    async def run_tests(self, endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """运行所有测试
        
        参数:
            endpoints: 要测试的端点列表，每个元素是包含endpoint、method和data的字典
            
        返回:
            字典，包含所有测试结果
        """
        logger.info(f"开始性能测试，并发: {self.concurrency}, 总请求数/端点: {self.requests_count}")
        
        start_time = time.time()
        results = []
        
        # 限制并发请求数
        semaphore = asyncio.Semaphore(self.concurrency)
        
        async def run_with_semaphore(endpoint_info):
            async with semaphore:
                return await self._run_test_for_endpoint(
                    endpoint_info['endpoint'], 
                    endpoint_info.get('method', 'GET'),
                    endpoint_info.get('data'),
                    None  # session
                )
        
        # 创建任务并运行
        tasks = [run_with_semaphore(ep) for ep in endpoints]
        endpoint_results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_test_time = end_time - start_time
        
        # 汇总结果
        total_requests = sum(r['total_requests'] for r in endpoint_results)
        successful_requests = sum(r['successful_requests'] for r in endpoint_results)
        
        summary = {
            "test_time": datetime.now().isoformat(),
            "host": self.host,
            "port": self.port,
            "concurrency": self.concurrency,
            "total_test_time": total_test_time,
            "total_endpoints": len(endpoints),
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "endpoints": endpoint_results
        }
        
        # 保存结果
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"性能测试完成，总时间: {total_test_time:.2f}秒")
        logger.info(f"结果已保存到: {self.output_file}")
        
        return summary


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="API性能测试工具")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"API主机 (默认: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"API端口 (默认: {DEFAULT_PORT})")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY, 
                        help=f"并发请求数 (默认: {DEFAULT_CONCURRENCY})")
    parser.add_argument("--requests", type=int, default=DEFAULT_REQUESTS, 
                        help=f"每个端点的请求数 (默认: {DEFAULT_REQUESTS})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, 
                        help=f"请求超时时间（秒）(默认: {DEFAULT_TIMEOUT})")
    parser.add_argument("--auth", default=DEFAULT_AUTH, 
                        help="授权令牌，可以是Bearer token或API key")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, 
                        help=f"结果输出文件 (默认: {DEFAULT_OUTPUT})")
    args = parser.parse_args()
    
    # 设置要测试的端点
    endpoints = [
        {"endpoint": "/api/v1/health", "method": "GET"},
        {"endpoint": "/api/v1/auth/login", "method": "POST", "data": {"username": "admin", "password": "admin"}},
        {"endpoint": "/api/v1/models", "method": "GET"},
        {"endpoint": "/api/v1/users/me", "method": "GET"}
    ]
    
    tester = APIPerformanceTester(
        host=args.host,
        port=args.port,
        concurrency=args.concurrency,
        requests_count=args.requests,
        timeout=args.timeout,
        auth_token=args.auth,
        output_file=args.output
    )
    
    await tester.run_tests(endpoints)

if __name__ == "__main__":
    asyncio.run(main()) 