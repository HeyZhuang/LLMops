#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新管理员邮箱格式
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

# 更新邮箱SQL
update_sql = """
UPDATE account 
SET email = 'admin@llmops.com' 
WHERE email = 'admin@llmops.local';
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
    cursor.execute(update_sql)
    conn.commit()
    
    print("✅ 管理员邮箱更新成功!")
    print("新邮箱: admin@llmops.com")
    print("密码: admin123")
    
except Exception as e:
    print(f"❌ 更新邮箱失败: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
