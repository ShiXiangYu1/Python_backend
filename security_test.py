#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
安全测试脚本

用于测试应用的安全性，包括认证、注入攻击、XSS、CSRF等。
"""

import json
import time
import requests
import html
import re
from urllib.parse import quote

# 测试配置
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
TEST_USER = {"username": "sxy", "password": "sxy123456"}
RESULTS = {}
TOKEN = None

def login():
    """登录并获取认证令牌"""
    global TOKEN
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login/json",
            json=TEST_USER,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            TOKEN = response.json().get("access_token")
            print(f"✅ 登录成功，获取到令牌")
            return True
        else:
            print(f"❌ 登录失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 登录过程发生错误: {str(e)}")
        return False

def test_authentication():
    """测试认证机制"""
    print("\n🔒 测试认证机制...")
    results = []
    
    # 测试1: 未认证访问需要认证的端点
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/users/me")
        if response.status_code == 401:
            results.append({
                "name": "未认证访问保护资源",
                "status": "通过",
                "details": "未认证请求被正确拒绝"
            })
        else:
            results.append({
                "name": "未认证访问保护资源",
                "status": "失败",
                "details": f"未认证请求返回了非401状态码: {response.status_code}"
            })
    except Exception as e:
        results.append({
            "name": "未认证访问保护资源",
            "status": "错误",
            "details": f"测试过程发生错误: {str(e)}"
        })
    
    # 测试2: 使用错误的认证令牌
    try:
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/users/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        if response.status_code == 401:
            results.append({
                "name": "无效令牌认证",
                "status": "通过",
                "details": "无效令牌被正确拒绝"
            })
        else:
            results.append({
                "name": "无效令牌认证",
                "status": "失败",
                "details": f"无效令牌请求返回了非401状态码: {response.status_code}"
            })
    except Exception as e:
        results.append({
            "name": "无效令牌认证",
            "status": "错误",
            "details": f"测试过程发生错误: {str(e)}"
        })
    
    # 测试3: 使用有效的认证令牌
    if TOKEN:
        try:
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/users/me",
                headers={"Authorization": f"Bearer {TOKEN}"}
            )
            if response.status_code == 200:
                results.append({
                    "name": "有效令牌认证",
                    "status": "通过",
                    "details": "有效令牌被正确接受"
                })
            else:
                results.append({
                    "name": "有效令牌认证",
                    "status": "失败",
                    "details": f"有效令牌请求返回了非200状态码: {response.status_code}"
                })
        except Exception as e:
            results.append({
                "name": "有效令牌认证",
                "status": "错误",
                "details": f"测试过程发生错误: {str(e)}"
            })
    
    # 测试4: 登录尝试暴力破解防护
    try:
        start_time = time.time()
        consecutive_failures = 0
        
        for i in range(5):
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/auth/login/json",
                json={"username": TEST_USER["username"], "password": "wrong_password"},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                consecutive_failures += 1
            
            # 检查是否有延迟或锁定
            if i > 0 and response.elapsed.total_seconds() > 1.0:
                results.append({
                    "name": "暴力破解防护",
                    "status": "通过",
                    "details": f"检测到延迟响应机制，响应时间: {response.elapsed.total_seconds():.2f}秒"
                })
                break
            
        if consecutive_failures == 5:
            end_time = time.time()
            if end_time - start_time > 5.0:
                results.append({
                    "name": "暴力破解防护",
                    "status": "通过",
                    "details": "检测到延迟或防护机制"
                })
            else:
                results.append({
                    "name": "暴力破解防护",
                    "status": "警告",
                    "details": "连续5次错误登录没有检测到延迟或锁定机制"
                })
        
    except Exception as e:
        results.append({
            "name": "暴力破解防护",
            "status": "错误",
            "details": f"测试过程发生错误: {str(e)}"
        })
    
    RESULTS["authentication"] = results
    
    # 打印测试结果
    for result in results:
        status_icon = "✅" if result["status"] == "通过" else "⚠️" if result["status"] == "警告" else "❌"
        print(f"{status_icon} {result['name']}: {result['status']} - {result['details']}")

def test_injection():
    """测试SQL注入和命令注入漏洞"""
    print("\n💉 测试注入漏洞...")
    results = []
    
    # SQL注入测试向量
    sql_vectors = [
        "' OR '1'='1",
        "admin' --",
        "1'; DROP TABLE users; --",
        "1' UNION SELECT username, password FROM users --"
    ]
    
    # 命令注入测试向量
    cmd_vectors = [
        "; ls -la",
        "& dir",
        "| cat /etc/passwd",
        "`cat /etc/passwd`"
    ]
    
    # 测试1: 登录处的SQL注入
    for vector in sql_vectors:
        try:
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/auth/login",
                data={"username": vector, "password": "anypassword"}
            )
            
            # 正常情况下，注入应该失败或返回错误
            if response.status_code != 200:
                results.append({
                    "name": f"登录SQL注入 ({vector})",
                    "status": "通过",
                    "details": "登录端点正确处理了SQL注入尝试"
                })
            else:
                results.append({
                    "name": f"登录SQL注入 ({vector})",
                    "status": "警告",
                    "details": "SQL注入尝试返回了200状态码，可能存在漏洞"
                })
        except Exception as e:
            results.append({
                "name": f"登录SQL注入 ({vector})",
                "status": "错误",
                "details": f"测试过程发生错误: {str(e)}"
            })
    
    # 测试2: 查询参数的注入
    if TOKEN:
        for vector in sql_vectors + cmd_vectors:
            try:
                response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/models?search={quote(vector)}",
                    headers={"Authorization": f"Bearer {TOKEN}"}
                )
                
                # 检查响应中是否包含异常错误信息
                response_text = response.text.lower()
                suspicious_terms = ["sql", "syntax", "error", "exception", "odbc", "mysql", 
                                    "postgres", "sqlite", "database", "stack trace"]
                
                is_suspicious = any(term in response_text for term in suspicious_terms)
                
                if is_suspicious:
                    results.append({
                        "name": f"查询参数注入 ({vector})",
                        "status": "警告",
                        "details": "响应中包含可疑的错误信息，可能存在漏洞"
                    })
                else:
                    results.append({
                        "name": f"查询参数注入 ({vector})",
                        "status": "通过",
                        "details": "查询参数注入尝试被正确处理"
                    })
            except Exception as e:
                results.append({
                    "name": f"查询参数注入 ({vector})",
                    "status": "错误",
                    "details": f"测试过程发生错误: {str(e)}"
                })
    
    RESULTS["injection"] = results
    
    # 打印测试结果
    for result in results:
        status_icon = "✅" if result["status"] == "通过" else "⚠️" if result["status"] == "警告" else "❌"
        print(f"{status_icon} {result['name']}: {result['status']} - {result['details']}")

def test_xss():
    """测试跨站脚本(XSS)漏洞"""
    print("\n🔀 测试XSS漏洞...")
    results = []
    
    # XSS测试向量
    xss_vectors = [
        "<script>alert('XSS')</script>",
        "<img src='x' onerror='alert(\"XSS\")'>",
        "<div onmouseover='alert(\"XSS\")'>XSS Test</div>",
        "javascript:alert('XSS')"
    ]
    
    # 通过注册用户名测试存储型XSS
    for vector in xss_vectors:
        try:
            # 尝试注册带有XSS的用户名
            username = f"test_user_{int(time.time())}"
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/auth/register",
                json={
                    "username": username,
                    "email": f"{username}@example.com",
                    "password": "Password123!",
                    "confirm_password": "Password123!",
                    "full_name": vector
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200 or response.status_code == 201:
                # 注册成功，检查返回的用户信息是否转义了XSS向量
                response_json = response.json()
                full_name = response_json.get("full_name", "")
                
                if full_name and full_name == vector:
                    # 向量没有被转义或过滤
                    if "<" in full_name or ">" in full_name or "javascript:" in full_name:
                        results.append({
                            "name": f"存储型XSS ({vector})",
                            "status": "警告",
                            "details": "XSS向量在响应中未被转义或过滤"
                        })
                    else:
                        results.append({
                            "name": f"存储型XSS ({vector})",
                            "status": "通过",
                            "details": "XSS向量在响应中被正确处理"
                        })
                else:
                    # 向量被过滤或转义
                    results.append({
                        "name": f"存储型XSS ({vector})",
                        "status": "通过",
                        "details": "XSS向量在响应中被正确处理"
                    })
            else:
                # 可能是重复用户名或其他问题
                results.append({
                    "name": f"存储型XSS ({vector})",
                    "status": "跳过",
                    "details": f"无法注册用户，状态码: {response.status_code}"
                })
        except Exception as e:
            results.append({
                "name": f"存储型XSS ({vector})",
                "status": "错误",
                "details": f"测试过程发生错误: {str(e)}"
            })
    
    # 通过查询参数测试反射型XSS
    if TOKEN:
        for vector in xss_vectors:
            try:
                response = requests.get(
                    f"{BASE_URL}/search?q={quote(vector)}",
                    headers={"Authorization": f"Bearer {TOKEN}"}
                )
                
                if response.status_code == 200:
                    # 检查响应中是否包含未转义的XSS向量
                    response_text = response.text
                    if vector in response_text and not html.escape(vector) in response_text:
                        results.append({
                            "name": f"反射型XSS ({vector})",
                            "status": "警告",
                            "details": "XSS向量在响应中未被转义或过滤"
                        })
                    else:
                        results.append({
                            "name": f"反射型XSS ({vector})",
                            "status": "通过",
                            "details": "XSS向量在响应中被正确处理"
                        })
                else:
                    # 端点不存在或其他问题
                    results.append({
                        "name": f"反射型XSS ({vector})",
                        "status": "跳过",
                        "details": f"无法访问搜索页面，状态码: {response.status_code}"
                    })
            except Exception as e:
                results.append({
                    "name": f"反射型XSS ({vector})",
                    "status": "错误",
                    "details": f"测试过程发生错误: {str(e)}"
                })
    
    RESULTS["xss"] = results
    
    # 打印测试结果
    for result in results:
        status_icon = "✅" if result["status"] == "通过" else "⚠️" if result["status"] == "警告" else "⏭️" if result["status"] == "跳过" else "❌"
        print(f"{status_icon} {result['name']}: {result['status']} - {result['details']}")

def test_csrf():
    """测试跨站请求伪造(CSRF)防护"""
    print("\n🛡️ 测试CSRF防护...")
    results = []
    
    # 测试1: 检查API是否使用CSRF令牌
    try:
        # 获取用户信息页面，查找CSRF令牌
        response = requests.get(
            f"{BASE_URL}/dashboard",
            headers={"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
        )
        
        if response.status_code == 200:
            # 检查响应中是否包含CSRF令牌
            csrf_pattern = re.compile(r'<input[^>]*name=["\'](csrf_token|_csrf|csrfmiddlewaretoken)["\'][^>]*value=["\'](.*?)["\']', re.IGNORECASE)
            match = csrf_pattern.search(response.text)
            
            if match:
                csrf_token = match.group(2)
                results.append({
                    "name": "CSRF令牌存在",
                    "status": "通过",
                    "details": "在响应中找到CSRF令牌"
                })
                
                # 测试2: 使用CSRF令牌发送请求
                try:
                    if TOKEN:
                        # 尝试使用CSRF令牌更新用户资料
                        csrf_response = requests.post(
                            f"{BASE_URL}/profile/update",
                            data={
                                match.group(1): csrf_token,  # CSRF令牌
                                "full_name": "CSRF Test"
                            },
                            headers={
                                "Authorization": f"Bearer {TOKEN}",
                                "Referer": f"{BASE_URL}/dashboard"
                            }
                        )
                        
                        if csrf_response.status_code != 403:
                            results.append({
                                "name": "CSRF令牌验证",
                                "status": "通过",
                                "details": "带有CSRF令牌的请求被接受"
                            })
                        else:
                            results.append({
                                "name": "CSRF令牌验证",
                                "status": "失败",
                                "details": "带有CSRF令牌的请求被拒绝"
                            })
                        
                        # 测试3: 不使用CSRF令牌发送请求
                        no_csrf_response = requests.post(
                            f"{BASE_URL}/profile/update",
                            data={"full_name": "CSRF Test No Token"},
                            headers={
                                "Authorization": f"Bearer {TOKEN}",
                                "Referer": f"{BASE_URL}/dashboard"
                            }
                        )
                        
                        if no_csrf_response.status_code == 403:
                            results.append({
                                "name": "CSRF保护",
                                "status": "通过",
                                "details": "没有CSRF令牌的请求被正确拒绝"
                            })
                        else:
                            results.append({
                                "name": "CSRF保护",
                                "status": "警告",
                                "details": "没有CSRF令牌的请求被接受，可能存在CSRF漏洞"
                            })
                except Exception as e:
                    results.append({
                        "name": "CSRF请求测试",
                        "status": "错误",
                        "details": f"测试过程发生错误: {str(e)}"
                    })
            else:
                results.append({
                    "name": "CSRF令牌存在",
                    "status": "警告",
                    "details": "在响应中未找到CSRF令牌，可能缺少CSRF保护"
                })
        else:
            results.append({
                "name": "CSRF页面访问",
                "status": "跳过",
                "details": f"无法访问用户信息页面，状态码: {response.status_code}"
            })
    except Exception as e:
        results.append({
            "name": "CSRF测试",
            "status": "错误",
            "details": f"测试过程发生错误: {str(e)}"
        })
    
    # 测试4: 测试SameSite Cookies
    try:
        # 发送请求并检查Set-Cookie头
        response = requests.get(f"{BASE_URL}/")
        
        if 'set-cookie' in response.headers:
            cookies = response.headers.get('set-cookie')
            samesite_pattern = re.compile(r'samesite=(strict|lax|none)', re.IGNORECASE)
            match = samesite_pattern.search(cookies)
            
            if match:
                samesite_value = match.group(1).lower()
                if samesite_value == 'strict' or samesite_value == 'lax':
                    results.append({
                        "name": "SameSite Cookies",
                        "status": "通过",
                        "details": f"SameSite属性设置为{samesite_value}"
                    })
                elif samesite_value == 'none':
                    results.append({
                        "name": "SameSite Cookies",
                        "status": "警告",
                        "details": "SameSite属性设置为None，可能导致CSRF风险"
                    })
            else:
                results.append({
                    "name": "SameSite Cookies",
                    "status": "警告",
                    "details": "Cookie未设置SameSite属性，可能导致CSRF风险"
                })
        else:
            results.append({
                "name": "SameSite Cookies",
                "status": "跳过",
                "details": "响应中没有Set-Cookie头"
            })
    except Exception as e:
        results.append({
            "name": "SameSite Cookies测试",
            "status": "错误",
            "details": f"测试过程发生错误: {str(e)}"
        })
    
    RESULTS["csrf"] = results
    
    # 打印测试结果
    for result in results:
        status_icon = "✅" if result["status"] == "通过" else "⚠️" if result["status"] == "警告" else "⏭️" if result["status"] == "跳过" else "❌"
        print(f"{status_icon} {result['name']}: {result['status']} - {result['details']}")

def test_headers():
    """测试安全相关的HTTP头"""
    print("\n📋 测试安全HTTP头...")
    results = []
    
    try:
        response = requests.get(f"{BASE_URL}/")
        headers = response.headers
        
        # 测试1: X-XSS-Protection
        if 'X-XSS-Protection' in headers:
            xss_protection = headers['X-XSS-Protection']
            if xss_protection == '1; mode=block':
                results.append({
                    "name": "X-XSS-Protection",
                    "status": "通过",
                    "details": "X-XSS-Protection设置为1; mode=block"
                })
            else:
                results.append({
                    "name": "X-XSS-Protection",
                    "status": "警告",
                    "details": f"X-XSS-Protection值不是推荐的配置: {xss_protection}"
                })
        else:
            results.append({
                "name": "X-XSS-Protection",
                "status": "警告",
                "details": "未设置X-XSS-Protection头"
            })
        
        # 测试2: X-Content-Type-Options
        if 'X-Content-Type-Options' in headers:
            content_type_options = headers['X-Content-Type-Options']
            if content_type_options.lower() == 'nosniff':
                results.append({
                    "name": "X-Content-Type-Options",
                    "status": "通过",
                    "details": "X-Content-Type-Options设置为nosniff"
                })
            else:
                results.append({
                    "name": "X-Content-Type-Options",
                    "status": "警告",
                    "details": f"X-Content-Type-Options值不是推荐的配置: {content_type_options}"
                })
        else:
            results.append({
                "name": "X-Content-Type-Options",
                "status": "警告",
                "details": "未设置X-Content-Type-Options头"
            })
        
        # 测试3: X-Frame-Options
        if 'X-Frame-Options' in headers:
            frame_options = headers['X-Frame-Options'].upper()
            if frame_options in ['DENY', 'SAMEORIGIN']:
                results.append({
                    "name": "X-Frame-Options",
                    "status": "通过",
                    "details": f"X-Frame-Options设置为{frame_options}"
                })
            else:
                results.append({
                    "name": "X-Frame-Options",
                    "status": "警告",
                    "details": f"X-Frame-Options值不是推荐的配置: {frame_options}"
                })
        else:
            results.append({
                "name": "X-Frame-Options",
                "status": "警告",
                "details": "未设置X-Frame-Options头"
            })
        
        # 测试4: Content-Security-Policy
        if 'Content-Security-Policy' in headers:
            csp = headers['Content-Security-Policy']
            results.append({
                "name": "Content-Security-Policy",
                "status": "通过",
                "details": "已设置Content-Security-Policy头"
            })
        else:
            results.append({
                "name": "Content-Security-Policy",
                "status": "警告",
                "details": "未设置Content-Security-Policy头"
            })
        
        # 测试5: Strict-Transport-Security (HSTS)
        if 'Strict-Transport-Security' in headers:
            hsts = headers['Strict-Transport-Security']
            if 'max-age=' in hsts and int(re.search(r'max-age=(\d+)', hsts).group(1)) >= 31536000:
                results.append({
                    "name": "Strict-Transport-Security",
                    "status": "通过",
                    "details": f"已设置HSTS头，max-age至少一年"
                })
            else:
                results.append({
                    "name": "Strict-Transport-Security",
                    "status": "警告",
                    "details": f"HSTS头存在但配置不理想: {hsts}"
                })
        else:
            results.append({
                "name": "Strict-Transport-Security",
                "status": "警告",
                "details": "未设置HSTS头"
            })
        
        # 测试6: 服务器信息泄露
        if 'Server' in headers:
            server = headers['Server']
            if len(server) > 0 and not server.lower() == 'uvicorn':
                results.append({
                    "name": "服务器信息泄露",
                    "status": "警告",
                    "details": f"Server头泄露了详细的服务器信息: {server}"
                })
            else:
                results.append({
                    "name": "服务器信息泄露",
                    "status": "通过",
                    "details": "Server头未泄露详细的服务器信息"
                })
        else:
            results.append({
                "name": "服务器信息泄露",
                "status": "通过",
                "details": "未设置Server头"
            })
        
    except Exception as e:
        results.append({
            "name": "HTTP头测试",
            "status": "错误",
            "details": f"测试过程发生错误: {str(e)}"
        })
    
    RESULTS["headers"] = results
    
    # 打印测试结果
    for result in results:
        status_icon = "✅" if result["status"] == "通过" else "⚠️" if result["status"] == "警告" else "⏭️" if result["status"] == "跳过" else "❌"
        print(f"{status_icon} {result['name']}: {result['status']} - {result['details']}")

def generate_report():
    """生成安全测试报告"""
    print("\n📊 生成安全测试报告...")
    
    # 保存结果为JSON
    with open("security_test_results.json", "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, indent=2, ensure_ascii=False)
    
    # 生成文本报告
    with open("security_test_report.txt", "w", encoding="utf-8") as f:
        f.write("API安全测试报告\n")
        f.write("=" * 50 + "\n\n")
        
        # 计算总体统计
        total_tests = 0
        passed_tests = 0
        warning_tests = 0
        failed_tests = 0
        skipped_tests = 0
        error_tests = 0
        
        for category, tests in RESULTS.items():
            for test in tests:
                total_tests += 1
                if test["status"] == "通过":
                    passed_tests += 1
                elif test["status"] == "警告":
                    warning_tests += 1
                elif test["status"] == "失败":
                    failed_tests += 1
                elif test["status"] == "跳过":
                    skipped_tests += 1
                else:
                    error_tests += 1
        
        # 写入总体统计
        f.write("统计摘要:\n")
        f.write("-" * 50 + "\n")
        f.write(f"总测试数: {total_tests}\n")
        f.write(f"通过: {passed_tests} ({passed_tests/total_tests*100:.2f}%)\n")
        f.write(f"警告: {warning_tests} ({warning_tests/total_tests*100:.2f}%)\n")
        f.write(f"失败: {failed_tests} ({failed_tests/total_tests*100:.2f}%)\n")
        f.write(f"跳过: {skipped_tests} ({skipped_tests/total_tests*100:.2f}%)\n")
        f.write(f"错误: {error_tests} ({error_tests/total_tests*100:.2f}%)\n\n")
        
        # 计算安全评级
        security_score = (passed_tests * 100) / (total_tests - skipped_tests) if (total_tests - skipped_tests) > 0 else 0
        
        if security_score >= 90:
            security_rating = "A (优秀)"
            recommendation = "系统安全性良好，可以考虑进一步加强内容安全策略和HSTS配置。"
        elif security_score >= 80:
            security_rating = "B (良好)"
            recommendation = "系统整体安全，但存在一些警告项需要改进，特别是HTTP安全头配置。"
        elif security_score >= 70:
            security_rating = "C (一般)"
            recommendation = "系统存在多个安全警告，建议优先修复XSS和CSRF防护问题。"
        elif security_score >= 60:
            security_rating = "D (较差)"
            recommendation = "系统安全性较差，存在多个高风险漏洞，需要尽快修复。"
        else:
            security_rating = "F (不及格)"
            recommendation = "系统安全性极差，存在严重漏洞，建议立即进行全面安全审计和修复。"
        
        f.write(f"安全评级: {security_rating}\n")
        f.write(f"安全得分: {security_score:.2f}/100\n")
        f.write(f"建议: {recommendation}\n\n")
        
        # 写入详细测试结果
        for category, tests in RESULTS.items():
            if category == "authentication":
                f.write("\n认证机制测试:\n")
            elif category == "injection":
                f.write("\n注入漏洞测试:\n")
            elif category == "xss":
                f.write("\nXSS漏洞测试:\n")
            elif category == "csrf":
                f.write("\nCSRF防护测试:\n")
            elif category == "headers":
                f.write("\n安全HTTP头测试:\n")
            else:
                f.write(f"\n{category}测试:\n")
            
            f.write("-" * 50 + "\n")
            
            for test in tests:
                status_symbol = "✓" if test["status"] == "通过" else "!" if test["status"] == "警告" else "✗" if test["status"] == "失败" else "-" if test["status"] == "跳过" else "?"
                f.write(f"[{status_symbol}] {test['name']}: {test['status']}\n")
                f.write(f"    {test['details']}\n\n")
    
    print("✅ 已生成安全测试报告: security_test_report.txt")

def main():
    """主函数"""
    print("🚀 开始API安全测试...")
    
    # 登录获取令牌
    login()
    
    # 执行安全测试
    test_authentication()
    test_injection()
    test_xss()
    test_csrf()
    test_headers()
    
    # 生成报告
    generate_report()
    
    print("\n✅ 安全测试完成!")

if __name__ == "__main__":
    main() 