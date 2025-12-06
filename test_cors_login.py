#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试CORS和登录功能
"""
import requests
import json

# 测试配置
API_BASE = "http://localhost:5000"
LOGIN_URL = f"{API_BASE}/auth/password-login"

# 测试数据
login_data = {
    "email": "admin@llmops.com",
    "password": "admin123"
}

def test_cors_and_login():
    print("🔍 测试CORS和登录功能")
    print("=" * 50)
    
    try:
        # 测试OPTIONS请求（CORS预检）
        print("1. 测试CORS预检请求...")
        options_response = requests.options(LOGIN_URL)
        print(f"   OPTIONS状态码: {options_response.status_code}")
        print(f"   CORS头信息: {dict(options_response.headers)}")
        
        # 测试登录请求
        print("\n2. 测试登录请求...")
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'http://localhost:5173'
        }
        
        response = requests.post(
            LOGIN_URL, 
            json=login_data,
            headers=headers
        )
        
        print(f"   POST状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
                print("✅ 登录测试成功!")
            except json.JSONDecodeError:
                print(f"   响应内容: {response.text}")
        else:
            print(f"   错误响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保后端服务正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_cors_and_login()
