#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
性能测试脚本

用于测试API的性能，包括响应时间、并发处理能力、数据库性能等。
"""

import json
import time
import asyncio
import statistics
import aiohttp
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import psutil
import platform
import os
import csv

# 测试配置
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
TEST_USER = {"username": "sxy", "password": "sxy123456"}
RESULTS = {}
TOKEN = None
MAX_CONCURRENT_REQUESTS = 50
REQUEST_COUNT = 200
TEST_ENDPOINTS = [
    {"name": "获取当前用户", "method": "GET", "path": "/users/me", "auth_required": True},
    {"name": "获取AI模型列表", "method": "GET", "path": "/models", "auth_required": True},
    {"name": "健康检查", "method": "GET", "path": "/health", "auth_required": False},
]
CSV_RESULT_FILE = "performance_results.csv"
CHART_RESULT_FILE = "performance_results.png"
REPORT_FILE = "performance_report.md"

async def login():
    """登录并获取认证令牌"""
    global TOKEN
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}{API_PREFIX}/auth/login/json",
                json=TEST_USER,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    TOKEN = data.get("access_token")
                    print(f"✅ 登录成功，获取到令牌")
                    return True
                else:
                    print(f"❌ 登录失败: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 登录过程发生错误: {str(e)}")
            return False

async def make_request(session, endpoint, request_id):
    """发送单个请求，并记录性能指标"""
    method = endpoint["method"]
    path = endpoint["path"]
    auth_required = endpoint["auth_required"]
    url = f"{BASE_URL}{API_PREFIX}{path}"
    
    headers = {}
    if auth_required and TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    
    start_time = time.time()
    try:
        if method == "GET":
            async with session.get(url, headers=headers) as response:
                response_time = time.time() - start_time
                status = response.status
                try:
                    # 尝试读取响应体的大小
                    response_data = await response.read()
                    size = len(response_data)
                except:
                    size = 0
                
                return {
                    "request_id": request_id,
                    "endpoint": endpoint["name"],
                    "status_code": status,
                    "response_time": response_time,
                    "size": size,
                    "success": 200 <= status < 400
                }
        elif method == "POST":
            async with session.post(url, headers=headers) as response:
                response_time = time.time() - start_time
                status = response.status
                try:
                    response_data = await response.read()
                    size = len(response_data)
                except:
                    size = 0
                
                return {
                    "request_id": request_id,
                    "endpoint": endpoint["name"],
                    "status_code": status,
                    "response_time": response_time,
                    "size": size,
                    "success": 200 <= status < 400
                }
    except Exception as e:
        response_time = time.time() - start_time
        return {
            "request_id": request_id,
            "endpoint": endpoint["name"],
            "status_code": 0,
            "response_time": response_time,
            "size": 0,
            "success": False,
            "error": str(e)
        }

async def run_load_test(endpoint, concurrency, request_count):
    """执行负载测试，并收集结果"""
    print(f"\n⚡ 测试端点: {endpoint['name']} (并发数: {concurrency}, 请求数: {request_count})")
    
    all_results = []
    semaphore = asyncio.Semaphore(concurrency)
    
    async def bounded_request(session, endpoint, request_id):
        async with semaphore:
            return await make_request(session, endpoint, request_id)
    
    async with aiohttp.ClientSession() as session:
        tasks = [bounded_request(session, endpoint, i) for i in range(request_count)]
        results = await asyncio.gather(*tasks)
        all_results.extend(results)
    
    # 分析结果
    response_times = [r["response_time"] for r in all_results if r["success"]]
    successful_requests = sum(1 for r in all_results if r["success"])
    failed_requests = sum(1 for r in all_results if not r["success"])
    
    if response_times:
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        p95_response_time = np.percentile(response_times, 95) if len(response_times) > 10 else max_response_time
        
        # 计算每秒请求数 (RPS)
        total_duration = max(response_times) - min(response_times) if len(response_times) > 1 else sum(response_times)
        rps = len(response_times) / total_duration if total_duration > 0 else 0
        
        print(f"✅ 成功请求: {successful_requests}/{request_count} ({successful_requests/request_count*100:.2f}%)")
        print(f"❌ 失败请求: {failed_requests}/{request_count} ({failed_requests/request_count*100:.2f}%)")
        print(f"⏱️ 平均响应时间: {avg_response_time*1000:.2f}ms")
        print(f"⏱️ 中位数响应时间: {median_response_time*1000:.2f}ms")
        print(f"⏱️ 最短响应时间: {min_response_time*1000:.2f}ms")
        print(f"⏱️ 最长响应时间: {max_response_time*1000:.2f}ms")
        print(f"⏱️ 95%响应时间: {p95_response_time*1000:.2f}ms")
        print(f"🚀 每秒请求数 (RPS): {rps:.2f}")
        
        return {
            "endpoint": endpoint["name"],
            "concurrency": concurrency,
            "request_count": request_count,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": successful_requests / request_count if request_count > 0 else 0,
            "avg_response_time": avg_response_time,
            "median_response_time": median_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "p95_response_time": p95_response_time,
            "rps": rps,
            "detailed_results": all_results
        }
    else:
        print(f"❌ 所有请求均失败")
        return {
            "endpoint": endpoint["name"],
            "concurrency": concurrency,
            "request_count": request_count,
            "successful_requests": 0,
            "failed_requests": failed_requests,
            "success_rate": 0,
            "avg_response_time": 0,
            "median_response_time": 0,
            "min_response_time": 0,
            "max_response_time": 0,
            "p95_response_time": 0,
            "rps": 0,
            "detailed_results": all_results
        }

async def monitor_system_resources(duration, interval=1):
    """监控系统资源使用情况"""
    print(f"\n📊 开始监控系统资源 (持续 {duration} 秒, 间隔 {interval} 秒)...")
    
    cpu_percentages = []
    memory_usages = []
    timestamps = []
    
    end_time = time.time() + duration
    while time.time() < end_time:
        # 收集CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_percentages.append(cpu_percent)
        
        # 收集内存使用情况
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        memory_usages.append(memory_usage)
        
        timestamps.append(time.time())
        
        print(f"CPU: {cpu_percent}% | RAM: {memory_usage}%")
        
        # 等待
        await asyncio.sleep(interval)
    
    return {
        "timestamps": timestamps,
        "cpu_percentages": cpu_percentages,
        "memory_usages": memory_usages,
        "avg_cpu": statistics.mean(cpu_percentages) if cpu_percentages else 0,
        "max_cpu": max(cpu_percentages) if cpu_percentages else 0,
        "avg_memory": statistics.mean(memory_usages) if memory_usages else 0,
        "max_memory": max(memory_usages) if memory_usages else 0
    }

async def test_endpoint_scaling(endpoint):
    """测试端点在不同并发级别下的性能表现"""
    print(f"\n📈 测试端点在不同并发级别下的表现: {endpoint['name']}")
    
    results = []
    concurrency_levels = [1, 5, 10, 20, 50]
    
    for concurrency in concurrency_levels:
        request_count = concurrency * 10
        result = await run_load_test(endpoint, concurrency, request_count)
        results.append(result)
    
    return results

async def test_response_time_stability(endpoint, requests=50, concurrency=10):
    """测试响应时间的稳定性"""
    print(f"\n🔍 测试响应时间稳定性: {endpoint['name']}")
    
    result = await run_load_test(endpoint, concurrency, requests)
    
    if result["successful_requests"] > 0:
        # 计算响应时间的标准差
        response_times = [r["response_time"] for r in result["detailed_results"] if r["success"]]
        if len(response_times) > 1:
            std_dev = statistics.stdev(response_times)
            cv = (std_dev / result["avg_response_time"]) * 100 if result["avg_response_time"] > 0 else 0
            
            print(f"📊 响应时间标准差: {std_dev*1000:.2f}ms")
            print(f"📊 变异系数: {cv:.2f}%")
            
            stability_rating = ""
            if cv < 10:
                stability_rating = "极佳"
            elif cv < 20:
                stability_rating = "良好"
            elif cv < 30:
                stability_rating = "一般"
            elif cv < 50:
                stability_rating = "不稳定"
            else:
                stability_rating = "极不稳定"
                
            print(f"📊 稳定性评级: {stability_rating}")
            
            result["std_dev"] = std_dev
            result["cv"] = cv
            result["stability_rating"] = stability_rating
        else:
            print("❌ 样本量不足，无法计算标准差")
    else:
        print("❌ 没有成功的请求，无法评估稳定性")
    
    return result

def generate_performance_charts(results):
    """生成性能测试图表"""
    print("\n📊 生成性能测试图表...")
    
    plt.figure(figsize=(15, 10))
    
    # 创建2x2的子图
    ax1 = plt.subplot(2, 2, 1)
    ax2 = plt.subplot(2, 2, 2)
    ax3 = plt.subplot(2, 2, 3)
    ax4 = plt.subplot(2, 2, 4)
    
    # 1. 响应时间比较
    endpoints = []
    avg_times = []
    p95_times = []
    
    for endpoint_name, endpoint_results in results["endpoint_results"].items():
        endpoints.append(endpoint_name)
        avg_times.append(endpoint_results["avg_response_time"] * 1000)  # 转换为毫秒
        p95_times.append(endpoint_results["p95_response_time"] * 1000)  # 转换为毫秒
    
    x = np.arange(len(endpoints))
    width = 0.35
    
    ax1.bar(x - width/2, avg_times, width, label='平均响应时间')
    ax1.bar(x + width/2, p95_times, width, label='95%响应时间')
    ax1.set_ylabel('响应时间 (ms)')
    ax1.set_title('各端点响应时间比较')
    ax1.set_xticks(x)
    ax1.set_xticklabels(endpoints, rotation=30, ha='right')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # 2. 每秒请求数比较
    rps_values = [results["endpoint_results"][endpoint]["rps"] for endpoint in endpoints]
    
    ax2.bar(endpoints, rps_values, color='orange')
    ax2.set_ylabel('请求/秒')
    ax2.set_title('各端点每秒处理请求数')
    ax2.set_xticklabels(endpoints, rotation=30, ha='right')
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    # 3. 成功率比较
    success_rates = [results["endpoint_results"][endpoint]["success_rate"] * 100 for endpoint in endpoints]
    
    ax3.bar(endpoints, success_rates, color='green')
    ax3.set_ylabel('成功率 (%)')
    ax3.set_title('各端点请求成功率')
    ax3.set_xticklabels(endpoints, rotation=30, ha='right')
    ax3.set_ylim(0, 100)
    ax3.grid(True, linestyle='--', alpha=0.7)
    
    # 4. 系统资源使用情况
    if "system_resources" in results:
        resources = results["system_resources"]
        time_points = range(len(resources["cpu_percentages"]))
        
        ax4.plot(time_points, resources["cpu_percentages"], label='CPU使用率', color='red')
        ax4.plot(time_points, resources["memory_usages"], label='内存使用率', color='blue')
        ax4.set_xlabel('时间 (秒)')
        ax4.set_ylabel('使用率 (%)')
        ax4.set_title('系统资源使用情况')
        ax4.legend()
        ax4.grid(True, linestyle='--', alpha=0.7)
        ax4.set_ylim(0, 100)
    
    plt.tight_layout()
    plt.savefig(CHART_RESULT_FILE)
    print(f"✅ 已生成图表: {CHART_RESULT_FILE}")

def export_to_csv(results):
    """将性能测试结果导出为CSV文件"""
    print(f"\n📊 导出测试结果到CSV: {CSV_RESULT_FILE}")
    
    with open(CSV_RESULT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'endpoint', 'concurrency', 'request_count', 'successful_requests', 
            'failed_requests', 'success_rate', 'avg_response_time_ms', 
            'median_response_time_ms', 'min_response_time_ms', 'max_response_time_ms', 
            'p95_response_time_ms', 'rps'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for endpoint_name, endpoint_result in results["endpoint_results"].items():
            writer.writerow({
                'endpoint': endpoint_name,
                'concurrency': endpoint_result.get('concurrency', ''),
                'request_count': endpoint_result.get('request_count', ''),
                'successful_requests': endpoint_result.get('successful_requests', 0),
                'failed_requests': endpoint_result.get('failed_requests', 0),
                'success_rate': f"{endpoint_result.get('success_rate', 0) * 100:.2f}%",
                'avg_response_time_ms': f"{endpoint_result.get('avg_response_time', 0) * 1000:.2f}",
                'median_response_time_ms': f"{endpoint_result.get('median_response_time', 0) * 1000:.2f}",
                'min_response_time_ms': f"{endpoint_result.get('min_response_time', 0) * 1000:.2f}",
                'max_response_time_ms': f"{endpoint_result.get('max_response_time', 0) * 1000:.2f}",
                'p95_response_time_ms': f"{endpoint_result.get('p95_response_time', 0) * 1000:.2f}",
                'rps': f"{endpoint_result.get('rps', 0):.2f}"
            })
    
    print(f"✅ 已导出CSV文件: {CSV_RESULT_FILE}")

def generate_performance_report(results):
    """生成性能测试报告"""
    print(f"\n📊 生成性能测试报告: {REPORT_FILE}")
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# API性能测试报告\n\n")
        
        # 写入测试信息
        f.write("## 测试信息\n\n")
        f.write(f"- **测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **测试环境**: {platform.system()} {platform.release()}\n")
        f.write(f"- **处理器**: {platform.processor()}\n")
        f.write(f"- **Python版本**: {platform.python_version()}\n")
        f.write(f"- **测试端点数**: {len(results['endpoint_results'])}\n")
        f.write(f"- **最大并发数**: {MAX_CONCURRENT_REQUESTS}\n\n")
        
        # 写入总体性能评估
        f.write("## 总体性能评估\n\n")
        
        # 计算平均响应时间和平均RPS
        avg_response_times = [endpoint_result["avg_response_time"] for endpoint_result in results["endpoint_results"].values()]
        avg_rps = [endpoint_result["rps"] for endpoint_result in results["endpoint_results"].values()]
        
        overall_avg_response_time = statistics.mean(avg_response_times) if avg_response_times else 0
        overall_avg_rps = statistics.mean(avg_rps) if avg_rps else 0
        
        # 性能评级
        performance_score = 0
        if overall_avg_response_time > 0:
            response_time_score = min(100, 100 / (overall_avg_response_time * 10)) 
            rps_score = min(100, overall_avg_rps * 2)
            performance_score = (response_time_score + rps_score) / 2
        
        if performance_score >= 90:
            performance_rating = "A (优秀)"
            recommendation = "系统性能表现优秀，可以考虑进一步优化缓存策略和数据库查询。"
        elif performance_score >= 80:
            performance_rating = "B (良好)"
            recommendation = "系统整体性能良好，但部分端点响应时间可能需要优化。"
        elif performance_score >= 70:
            performance_rating = "C (一般)"
            recommendation = "系统性能一般，需要着重优化慢查询和并发处理能力。"
        elif performance_score >= 60:
            performance_rating = "D (较差)"
            recommendation = "系统性能较差，存在明显的瓶颈，需要进行全面优化。"
        else:
            performance_rating = "F (不及格)"
            recommendation = "系统性能极差，建议重构架构或关键组件。"
        
        f.write(f"- **平均响应时间**: {overall_avg_response_time*1000:.2f}ms\n")
        f.write(f"- **平均每秒请求数**: {overall_avg_rps:.2f}\n")
        f.write(f"- **性能评级**: {performance_rating}\n")
        f.write(f"- **性能得分**: {performance_score:.2f}/100\n")
        f.write(f"- **建议**: {recommendation}\n\n")
        
        # 写入系统资源使用情况
        if "system_resources" in results:
            f.write("## 系统资源使用情况\n\n")
            resources = results["system_resources"]
            
            f.write(f"- **平均CPU使用率**: {resources['avg_cpu']:.2f}%\n")
            f.write(f"- **最大CPU使用率**: {resources['max_cpu']:.2f}%\n")
            f.write(f"- **平均内存使用率**: {resources['avg_memory']:.2f}%\n")
            f.write(f"- **最大内存使用率**: {resources['max_memory']:.2f}%\n\n")
        
        # 写入各端点性能详情
        f.write("## 各端点性能详情\n\n")
        
        for endpoint_name, endpoint_result in results["endpoint_results"].items():
            f.write(f"### {endpoint_name}\n\n")
            
            f.write(f"- **请求成功率**: {endpoint_result['success_rate']*100:.2f}%\n")
            f.write(f"- **平均响应时间**: {endpoint_result['avg_response_time']*1000:.2f}ms\n")
            f.write(f"- **中位数响应时间**: {endpoint_result['median_response_time']*1000:.2f}ms\n")
            f.write(f"- **最短响应时间**: {endpoint_result['min_response_time']*1000:.2f}ms\n")
            f.write(f"- **最长响应时间**: {endpoint_result['max_response_time']*1000:.2f}ms\n")
            f.write(f"- **95%响应时间**: {endpoint_result['p95_response_time']*1000:.2f}ms\n")
            f.write(f"- **每秒请求数(RPS)**: {endpoint_result['rps']:.2f}\n")
            
            if "stability_rating" in endpoint_result:
                f.write(f"- **响应时间标准差**: {endpoint_result['std_dev']*1000:.2f}ms\n")
                f.write(f"- **变异系数**: {endpoint_result['cv']:.2f}%\n")
                f.write(f"- **稳定性评级**: {endpoint_result['stability_rating']}\n")
            
            f.write("\n")
        
        # 写入性能瓶颈分析
        f.write("## 性能瓶颈分析\n\n")
        
        # 找出响应时间最长的端点
        slowest_endpoint = max(results["endpoint_results"].items(), key=lambda x: x[1]["avg_response_time"])
        f.write(f"- **最慢端点**: {slowest_endpoint[0]} (平均响应时间: {slowest_endpoint[1]['avg_response_time']*1000:.2f}ms)\n")
        
        # 找出RPS最低的端点
        lowest_rps_endpoint = min(results["endpoint_results"].items(), key=lambda x: x[1]["rps"])
        f.write(f"- **吞吐量最低端点**: {lowest_rps_endpoint[0]} (RPS: {lowest_rps_endpoint[1]['rps']:.2f})\n\n")
        
        if "system_resources" in results:
            resources = results["system_resources"]
            if resources["max_cpu"] > 80:
                f.write("- **CPU使用率过高**: 测试过程中CPU使用率超过80%，可能是性能瓶颈\n")
            if resources["max_memory"] > 80:
                f.write("- **内存使用率过高**: 测试过程中内存使用率超过80%，可能需要优化内存使用\n")
        
        # 写入优化建议
        f.write("\n## 优化建议\n\n")
        
        f.write("1. **数据库优化**:\n")
        f.write("   - 检查并优化慢查询\n")
        f.write("   - 为频繁查询的字段添加索引\n")
        f.write("   - 考虑使用数据库连接池\n\n")
        
        f.write("2. **缓存策略**:\n")
        f.write("   - 对热点数据实施缓存\n")
        f.write("   - 使用Redis缓存查询结果\n")
        f.write("   - 实现HTTP响应缓存\n\n")
        
        f.write("3. **代码优化**:\n")
        f.write("   - 优化耗时的业务逻辑\n")
        f.write("   - 使用异步处理非关键路径操作\n")
        f.write("   - 减少不必要的数据库查询\n\n")
        
        f.write("4. **并发处理**:\n")
        f.write("   - 增加应用实例数\n")
        f.write("   - 调整Uvicorn工作进程数\n")
        f.write("   - 使用负载均衡器分散请求\n\n")
        
        f.write("5. **监控与告警**:\n")
        f.write("   - 实施实时性能监控\n")
        f.write("   - 设置性能指标告警\n")
        f.write("   - 定期进行压力测试\n\n")
        
        f.write("## 附件\n\n")
        f.write(f"- [性能测试结果CSV]({CSV_RESULT_FILE})\n")
        f.write(f"- [性能测试图表]({CHART_RESULT_FILE})\n")
    
    print(f"✅ 已生成性能测试报告: {REPORT_FILE}")

async def main():
    """主函数"""
    print("🚀 开始API性能测试...")
    
    # 登录获取令牌
    login_success = await login()
    if not login_success:
        print("❌ 登录失败，无法继续测试需要认证的端点")
    
    # 测试结果
    all_results = {"endpoint_results": {}}
    
    # 并发测试每个端点
    for endpoint in TEST_ENDPOINTS:
        if endpoint["auth_required"] and not TOKEN:
            print(f"⏭️ 跳过需要认证的端点: {endpoint['name']}")
            continue
        
        # 1. 基本负载测试
        result = await run_load_test(endpoint, MAX_CONCURRENT_REQUESTS, REQUEST_COUNT)
        all_results["endpoint_results"][endpoint["name"]] = result
        
        # 2. 响应时间稳定性测试
        stability_result = await test_response_time_stability(endpoint)
        
        # 更新结果
        if "stability_rating" in stability_result:
            all_results["endpoint_results"][endpoint["name"]]["stability_rating"] = stability_result["stability_rating"]
            all_results["endpoint_results"][endpoint["name"]]["std_dev"] = stability_result["std_dev"]
            all_results["endpoint_results"][endpoint["name"]]["cv"] = stability_result["cv"]
    
    # 3. 系统资源监控
    resources = await monitor_system_resources(duration=10)
    all_results["system_resources"] = resources
    
    # 生成结果和报告
    generate_performance_charts(all_results)
    export_to_csv(all_results)
    generate_performance_report(all_results)
    
    print("\n✅ 性能测试完成! 请查看性能测试报告获取详细信息。")

if __name__ == "__main__":
    asyncio.run(main()) 