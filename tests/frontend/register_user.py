#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户注册脚本

用于注册新用户的简单Python脚本。
"""

import json
import requests

# 注册数据
register_data = {
    "username": "sxy",
    "email": "294802186@qq.com",
    "password": "sxy123456",
    "confirm_password": "sxy123456"
}

# API地址
register_url = "http://localhost:8000/api/v1/auth/register"

# 发送请求
try:
    response = requests.post(
        register_url,
        json=register_data,
        headers={"Content-Type": "application/json"}
    )
    
    # 打印响应
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    # 如果注册成功，显示账号信息
    if response.status_code == 200:
        print("\n注册成功! 账号信息:")
        print(f"用户名: {register_data['username']}")
        print(f"邮箱: {register_data['email']}")
        print(f"密码: {register_data['password']}")
    else:
        print("\n注册失败。请检查错误信息。")
        
except Exception as e:
    print(f"发生错误: {str(e)}") 