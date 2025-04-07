#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户登录测试脚本

用于测试用户登录功能的简单Python脚本。
"""

import json
import requests
import os

# 尝试加载刚刚注册的用户
new_user = None
if os.path.exists("last_registered_user.json"):
    try:
        with open("last_registered_user.json", "r", encoding="utf-8") as f:
            new_user = json.load(f)
        print(f"从文件加载了新注册用户: {new_user['username']}")
    except Exception as e:
        print(f"加载新用户失败: {str(e)}")

# 测试账号列表
test_accounts = [
    # 已有账号
    {
        "username": "sxy",
        "password": "sxy123456",
        "description": "已有账号"
    },
    {
        "username": "newuser123",
        "password": "password123",
        "description": "已有账号"
    }
]

# 添加新注册的用户到测试列表
if new_user:
    test_accounts.append({
        "username": new_user["username"],
        "password": new_user["password"],
        "description": "新注册用户"
    })

# 测试两种登录方式
def test_login(account):
    print(f"\n{'='*50}")
    print(f"正在测试账号: {account['username']} ({account['description']})")
    print(f"{'='*50}")
    
    # 1. 表单登录 /api/v1/auth/login
    print("\n方法1: 表单登录")
    try:
        form_data = {
            "username": account["username"],
            "password": account["password"]
        }
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            data=form_data  # 注意这里使用data而不是json
        )
        print(f"状态码: {response.status_code}")
        
        try:
            response_json = response.json()
            if "access_token" in response_json:
                # 只显示token的一部分
                token_preview = response_json["access_token"][:20] + "..." if response_json["access_token"] else ""
                print(f"响应内容: {{\"access_token\": \"{token_preview}\", \"token_type\": \"{response_json.get('token_type', '')}\"}}") 
                print("✅ 表单登录成功!")
            else:
                print(f"响应内容: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
        except:
            print(f"响应内容: {response.text}")
            
        # 检查登录状态
        if response.status_code == 200:
            token = response.json().get("access_token")
            if token:
                # 尝试获取用户信息
                print("\n尝试获取用户信息...")
                me_response = requests.get(
                    "http://localhost:8000/api/v1/users/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if me_response.status_code == 200:
                    user_info = me_response.json()
                    print(f"✅ 用户信息获取成功: {user_info.get('username')}")
                else:
                    print(f"❌ 用户信息获取失败: {me_response.status_code}")
    except Exception as e:
        print(f"❌ 表单登录发生错误: {str(e)}")
    
    # 2. JSON登录 /api/v1/auth/login/json
    print("\n方法2: JSON登录")
    try:
        login_data = {
            "username": account["username"],
            "password": account["password"]
        }
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login/json",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        
        try:
            response_json = response.json()
            if "access_token" in response_json:
                # 只显示token的一部分
                token_preview = response_json["access_token"][:20] + "..." if response_json["access_token"] else ""
                print(f"响应内容: {{\"access_token\": \"{token_preview}\", \"token_type\": \"{response_json.get('token_type', '')}\"}}") 
                print("✅ JSON登录成功!")
            else:
                print(f"响应内容: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
        except:
            print(f"响应内容: {response.text}")
            
        # 检查登录状态
        if response.status_code == 200:
            token = response.json().get("access_token")
            if token:
                # 尝试获取用户信息
                print("\n尝试获取用户信息...")
                me_response = requests.get(
                    "http://localhost:8000/api/v1/users/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if me_response.status_code == 200:
                    user_info = me_response.json()
                    print(f"✅ 用户信息获取成功: {user_info.get('username')}")
                else:
                    print(f"❌ 用户信息获取失败: {me_response.status_code}")
    except Exception as e:
        print(f"❌ JSON登录发生错误: {str(e)}")

# 测试所有账号
for account in test_accounts:
    test_login(account)

print("\n" + "="*50)
print("登录测试完成!")
print("="*50) 