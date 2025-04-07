#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
新用户注册测试脚本

用于测试用户注册功能的简单Python脚本。
"""

import json
import requests
import uuid
import time

# 生成随机用户名，避免冲突
random_suffix = str(uuid.uuid4())[:8]
timestamp = int(time.time())

# 注册数据
register_data = {
    "username": f"testuser_{random_suffix}",
    "email": f"testuser_{timestamp}@example.com",
    "password": "Test123456",
    "confirm_password": "Test123456"
}

# API地址
register_url = "http://localhost:8000/api/v1/auth/register"

# 发送请求
try:
    print(f"尝试注册用户: {register_data['username']}")
    print(f"用户数据: {json.dumps(register_data, ensure_ascii=False, indent=2)}")
    
    response = requests.post(
        register_url,
        json=register_data,
        headers={"Content-Type": "application/json"}
    )
    
    # 打印响应
    print(f"\n状态码: {response.status_code}")
    
    try:
        response_json = response.json()
        print(f"响应内容: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
    except:
        print(f"响应内容: {response.text}")
    
    # 如果注册成功，显示账号信息
    if response.status_code == 200:
        print("\n✅ 注册成功! 账号信息:")
        print(f"用户名: {register_data['username']}")
        print(f"邮箱: {register_data['email']}")
        print(f"密码: {register_data['password']}")
        
        # 保存用户信息到文件，方便后续测试
        with open("last_registered_user.json", "w", encoding="utf-8") as f:
            json.dump({
                "username": register_data['username'],
                "email": register_data['email'],
                "password": register_data['password']
            }, f, ensure_ascii=False, indent=2)
            print("\n用户信息已保存到 last_registered_user.json")
    else:
        print("\n❌ 注册失败。请检查错误信息。")
        
except Exception as e:
    print(f"发生错误: {str(e)}") 