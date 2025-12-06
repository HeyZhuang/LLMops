#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
执行管理员账号创建SQL
"""
import os
import psycopg2
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库连接参数
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_NAME = os.getenv('DB_NAME', 'llmops')

# 管理员账号SQL
admin_sql = """
INSERT INTO account (
    name,
    email,
    avatar,
    password,
    password_salt,
    last_login_at,
    last_login_ip,
    updated_at,
    created_at
) VALUES (
    'admin',
    'admin@llmops.local',
    '',
    '04106dfd3107465e00bc1248c23d4c53b34d7afdd51639cf73b7bfc1f33d4fd5',
    '3574704ed2093658762f54842b50e90d',
    CURRENT_TIMESTAMP,
    '127.0.0.1',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
"""

try:
    # 连接数据库
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    
    cursor = conn.cursor()
    
    # 执行SQL
    cursor.execute(admin_sql)
    conn.commit()
    
    print("✅ 管理员账号创建成功!")
    print("邮箱: admin@llmops.local")
    print("密码: admin123")
    
except psycopg2.IntegrityError as e:
    print("⚠️ 管理员账号可能已存在")
    print(f"错误: {e}")
except Exception as e:
    print(f"❌ 创建管理员账号失败: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
