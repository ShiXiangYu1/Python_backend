#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试运行主脚本

用于运行所有测试（性能测试、安全测试）并生成综合报告。
"""

import os
import sys
import time
import subprocess
import datetime
import argparse
import json
import platform
from pathlib import Path

# 测试脚本路径
PERFORMANCE_TEST = "performance_test.py"
SECURITY_TEST = "security_test.py"

# 报告路径
REPORTS_DIR = "test_reports"
COMBINED_REPORT = os.path.join(REPORTS_DIR, "combined_report.md")

# 确保所需的目录存在
os.makedirs(REPORTS_DIR, exist_ok=True)

def check_prerequisites():
    """检查运行测试所需的依赖"""
    print("📋 检查测试依赖...")
    
    required_modules = [
        "requests", "aiohttp", "matplotlib", "numpy", "psutil", 
        "statistics", "fastapi", "pytest", "asyncio"
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ 已安装 {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ 未安装 {module}")
    
    if missing_modules:
        print("\n⚠️ 请安装缺失的依赖:")
        print(f"pip install {' '.join(missing_modules)}")
        
        install = input("\n是否自动安装这些依赖? (y/n): ")
        if install.lower() == 'y':
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing_modules)
            print("✅ 依赖安装完成")
            return True
        else:
            print("⚠️ 请先安装缺失的依赖再运行测试")
            return False
    
    return True

def run_performance_test(args):
    """运行性能测试"""
    print("\n🚀 开始运行性能测试...")
    
    start_time = time.time()
    result = subprocess.run([sys.executable, PERFORMANCE_TEST], 
                          capture_output=True, text=True)
    elapsed_time = time.time() - start_time
    
    print(f"⏱️ 性能测试完成，耗时 {elapsed_time:.2f} 秒")
    
    if result.returncode != 0:
        print("❌ 性能测试失败:")
        print(result.stderr)
        return False
    else:
        if args.verbose:
            print(result.stdout)
        return True

def run_security_test(args):
    """运行安全测试"""
    print("\n🔒 开始运行安全测试...")
    
    start_time = time.time()
    result = subprocess.run([sys.executable, SECURITY_TEST], 
                          capture_output=True, text=True)
    elapsed_time = time.time() - start_time
    
    print(f"⏱️ 安全测试完成，耗时 {elapsed_time:.2f} 秒")
    
    if result.returncode != 0:
        print("❌ 安全测试失败:")
        print(result.stderr)
        return False
    else:
        if args.verbose:
            print(result.stdout)
        return True

def gather_test_results():
    """收集所有测试结果"""
    results = {}
    
    # 收集性能测试结果
    perf_report = Path("performance_report.md")
    perf_json = Path("performance_results.csv")
    perf_chart = Path("performance_results.png")
    
    # 收集安全测试结果
    security_report = Path("security_test_report.txt")
    security_json = Path("security_test_results.json")
    
    if perf_report.exists():
        with open(perf_report, "r", encoding="utf-8") as f:
            results["performance_report"] = f.read()
    
    if security_report.exists():
        with open(security_report, "r", encoding="utf-8") as f:
            results["security_report"] = f.read()
    
    if security_json.exists():
        with open(security_json, "r", encoding="utf-8") as f:
            results["security_results"] = json.load(f)
    
    return results

def generate_combined_report(results):
    """生成综合测试报告"""
    print("\n📊 生成综合测试报告...")
    
    report_path = Path(COMBINED_REPORT)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# API测试综合报告\n\n")
        
        # 写入测试信息
        f.write("## 测试信息\n\n")
        f.write(f"- **测试时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **测试环境**: {platform.system()} {platform.release()}\n")
        f.write(f"- **处理器**: {platform.processor()}\n")
        f.write(f"- **Python版本**: {platform.python_version()}\n\n")
        
        # 提取和计算总体评分
        overall_score = 0
        score_count = 0
        
        security_score = 0
        performance_score = 0
        
        # 1. 提取安全测试评分
        if "security_results" in results:
            security_data = results["security_results"]
            security_total = 0
            security_passed = 0
            security_skipped = 0
            
            for category, tests in security_data.items():
                for test in tests:
                    security_total += 1
                    if test["status"] == "通过":
                        security_passed += 1
                    elif test["status"] == "跳过":
                        security_skipped += 1
            
            if security_total > security_skipped:
                security_score = (security_passed * 100) / (security_total - security_skipped)
                overall_score += security_score
                score_count += 1
        
        # 2. 从性能测试报告中提取性能评分
        if "performance_report" in results:
            perf_report = results["performance_report"]
            
            # 寻找性能得分
            score_line = None
            for line in perf_report.split("\n"):
                if "性能得分" in line:
                    score_line = line
                    break
            
            if score_line:
                try:
                    score_str = score_line.split(":")[1].strip().split("/")[0]
                    performance_score = float(score_str)
                    overall_score += performance_score
                    score_count += 1
                except:
                    pass
        
        # 计算总体评分
        if score_count > 0:
            overall_score = overall_score / score_count
        
        # 确定总体评级
        if overall_score >= 90:
            overall_rating = "A (优秀)"
            overall_summary = "系统整体表现优秀，性能和安全性处于较高水平。"
        elif overall_score >= 80:
            overall_rating = "B (良好)"
            overall_summary = "系统整体表现良好，但在某些方面仍有优化空间。"
        elif overall_score >= 70:
            overall_rating = "C (一般)"
            overall_summary = "系统表现一般，需要在多个方面进行改进。"
        elif overall_score >= 60:
            overall_rating = "D (较差)"
            overall_summary = "系统表现较差，存在明显问题，需要全面优化。"
        else:
            overall_rating = "F (不及格)"
            overall_summary = "系统存在严重问题，需要重构或全面修复。"
        
        # 写入总体评估
        f.write("## 总体评估\n\n")
        f.write(f"- **总体评分**: {overall_score:.2f}/100\n")
        f.write(f"- **总体评级**: {overall_rating}\n")
        f.write(f"- **安全评分**: {security_score:.2f}/100\n")
        f.write(f"- **性能评分**: {performance_score:.2f}/100\n")
        f.write(f"- **总体评估**: {overall_summary}\n\n")
        
        # 添加主要发现和建议
        f.write("## 主要发现与建议\n\n")
        
        # 安全方面的主要发现
        f.write("### 安全性问题\n\n")
        if "security_results" in results:
            security_data = results["security_results"]
            warnings = []
            
            for category, tests in security_data.items():
                for test in tests:
                    if test["status"] == "警告" or test["status"] == "失败":
                        warnings.append({
                            "name": test["name"], 
                            "status": test["status"], 
                            "details": test["details"],
                            "category": category
                        })
            
            if warnings:
                for warning in warnings[:5]:  # 只显示前5个警告
                    f.write(f"- **{warning['name']}**: {warning['status']} - {warning['details']}\n")
            else:
                f.write("- 未发现显著的安全性问题\n")
        else:
            f.write("- 安全测试结果不可用\n")
        
        f.write("\n### 性能问题\n\n")
        # 从性能报告中提取关键信息
        if "performance_report" in results:
            perf_report = results["performance_report"]
            bottlenecks = []
            
            # 寻找瓶颈分析部分
            in_bottleneck_section = False
            for line in perf_report.split("\n"):
                if "## 性能瓶颈分析" in line:
                    in_bottleneck_section = True
                    continue
                
                if in_bottleneck_section and line.startswith("##"):
                    break
                
                if in_bottleneck_section and line.startswith("-"):
                    bottlenecks.append(line)
            
            if bottlenecks:
                for bottleneck in bottlenecks:
                    f.write(f"{bottleneck}\n")
            else:
                f.write("- 未发现显著的性能瓶颈\n")
        else:
            f.write("- 性能测试结果不可用\n")
        
        # 添加改进建议
        f.write("\n## 改进建议\n\n")
        
        # 安全性改进建议
        f.write("### 安全性改进\n\n")
        f.write("1. **实施更完善的认证机制**:\n")
        f.write("   - 添加防暴力破解措施，如账户锁定和延迟认证\n")
        f.write("   - 实施双因素认证\n")
        f.write("   - 强化密码策略\n\n")
        
        f.write("2. **加强HTTP安全头**:\n")
        f.write("   - 添加Content-Security-Policy头\n")
        f.write("   - 确保X-XSS-Protection设置为1; mode=block\n")
        f.write("   - 添加X-Content-Type-Options: nosniff\n")
        f.write("   - 配置Strict-Transport-Security头\n\n")
        
        f.write("3. **输入验证与输出转义**:\n")
        f.write("   - 对所有用户输入进行严格验证\n")
        f.write("   - 使用参数化查询防止SQL注入\n")
        f.write("   - 适当转义输出以防止XSS攻击\n\n")
        
        # 性能改进建议
        f.write("### 性能改进\n\n")
        if "performance_report" in results:
            perf_report = results["performance_report"]
            
            # 寻找优化建议部分
            in_optimization_section = False
            optimization_content = []
            
            for line in perf_report.split("\n"):
                if "## 优化建议" in line:
                    in_optimization_section = True
                    continue
                
                if in_optimization_section and line.startswith("##"):
                    break
                
                if in_optimization_section:
                    optimization_content.append(line)
            
            if optimization_content:
                f.write("".join(optimization_content))
            else:
                # 默认性能优化建议
                f.write("1. **优化数据库操作**:\n")
                f.write("   - 添加适当的索引\n")
                f.write("   - 优化查询语句\n")
                f.write("   - 实施数据库连接池\n\n")
                
                f.write("2. **添加缓存层**:\n")
                f.write("   - 对频繁访问的数据实施缓存\n")
                f.write("   - 使用Redis缓存会话和查询结果\n\n")
                
                f.write("3. **代码优化**:\n")
                f.write("   - 使用异步处理非阻塞操作\n")
                f.write("   - 优化计算密集型代码\n\n")
        else:
            # 默认性能优化建议
            f.write("1. **优化数据库操作**:\n")
            f.write("   - 添加适当的索引\n")
            f.write("   - 优化查询语句\n")
            f.write("   - 实施数据库连接池\n\n")
            
            f.write("2. **添加缓存层**:\n")
            f.write("   - 对频繁访问的数据实施缓存\n")
            f.write("   - 使用Redis缓存会话和查询结果\n\n")
            
            f.write("3. **代码优化**:\n")
            f.write("   - 使用异步处理非阻塞操作\n")
            f.write("   - 优化计算密集型代码\n\n")
        
        # 添加测试报告的链接
        f.write("\n## 详细测试报告\n\n")
        f.write("- [性能测试报告](performance_report.md)\n")
        f.write("- [性能测试结果图表](performance_results.png)\n")
        f.write("- [安全测试报告](security_test_report.txt)\n\n")
        
        # 添加结论
        f.write("## 结论\n\n")
        f.write("本次测试对API系统进行了全面的性能和安全性评估。")
        
        if overall_score >= 80:
            f.write("总体来看，系统表现良好，可以满足生产环境的需求。")
            f.write("建议定期进行类似的测试，以确保系统性能和安全性持续保持在高水平。\n\n")
        elif overall_score >= 60:
            f.write("系统存在一定的问题，需要根据上述建议进行改进。")
            f.write("建议在实施改进后再次进行测试，以验证改进效果。\n\n")
        else:
            f.write("系统存在严重问题，需要进行全面修复和优化。")
            f.write("建议暂缓系统上线，先解决测试中发现的关键问题。\n\n")
        
        f.write("\n\n---\n")
        f.write(f"*报告生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    print(f"✅ 综合报告已生成: {report_path}")
    
    # 复制报告和图表到报告目录
    report_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if Path("performance_report.md").exists():
        os.makedirs(os.path.join(REPORTS_DIR, "performance"), exist_ok=True)
        dst_path = os.path.join(REPORTS_DIR, "performance", f"performance_report_{report_time}.md")
        Path("performance_report.md").rename(dst_path)
    
    if Path("performance_results.png").exists():
        os.makedirs(os.path.join(REPORTS_DIR, "performance"), exist_ok=True)
        dst_path = os.path.join(REPORTS_DIR, "performance", f"performance_chart_{report_time}.png")
        Path("performance_results.png").rename(dst_path)
    
    if Path("security_test_report.txt").exists():
        os.makedirs(os.path.join(REPORTS_DIR, "security"), exist_ok=True)
        dst_path = os.path.join(REPORTS_DIR, "security", f"security_report_{report_time}.txt")
        Path("security_test_report.txt").rename(dst_path)
    
    if Path("security_test_results.json").exists():
        os.makedirs(os.path.join(REPORTS_DIR, "security"), exist_ok=True)
        dst_path = os.path.join(REPORTS_DIR, "security", f"security_results_{report_time}.json")
        Path("security_test_results.json").rename(dst_path)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行API测试套件")
    parser.add_argument("--performance", action="store_true", help="只运行性能测试")
    parser.add_argument("--security", action="store_true", help="只运行安全测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    parser.add_argument("--verbose", action="store_true", help="显示详细输出")
    args = parser.parse_args()
    
    # 默认运行所有测试
    if not (args.performance or args.security):
        args.all = True
    
    print("🚀 开始API测试...")
    
    # 检查依赖
    if not check_prerequisites():
        return
    
    # 运行测试
    if args.all or args.performance:
        run_performance_test(args)
    
    if args.all or args.security:
        run_security_test(args)
    
    # 生成报告
    results = gather_test_results()
    generate_combined_report(results)
    
    print("\n✅ 测试完成! 请查看测试报告获取详细信息。")

if __name__ == "__main__":
    main() 