#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户登录测试脚本

用于测试用户登录的简单Python脚本。
"""

import json
import requests

# 测试两个账号
test_accounts = [
    {
        "username": "newuser123",
        "password": "password123"
    },
    {
        "username": "sxy",
        "password": "sxy123456"
    }
]

# 测试两种登录方式
def test_login(account):
    print(f"\n正在测试账号: {account['username']}")
    
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
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"表单登录发生错误: {str(e)}")
    
    # 2. JSON登录 /api/v1/auth/login/json
    print("\n方法2: JSON登录")
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login/json",
            json=account,
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"JSON登录发生错误: {str(e)}")

# 测试所有账号
for account in test_accounts:
    test_login(account)

print("\n登录测试完成!") 