#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户创建脚本
用于在本地数据库中创建测试用户账号
"""
import os
import sys
import hashlib
import secrets
import dotenv
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def generate_password_hash(password: str, salt: str = None) -> tuple:
    """生成密码哈希和盐值"""
    if salt is None:
        salt = secrets.token_hex(16)  # 生成32字符的随机盐值
    
    # 使用 SHA-256 + 盐值进行密码哈希
    password_with_salt = password + salt
    password_hash = hashlib.sha256(password_with_salt.encode('utf-8')).hexdigest()
    
    return password_hash, salt

def create_user_sql(name: str, email: str, password: str, avatar: str = ""):
    """生成创建用户的SQL语句"""
    
    # 生成密码哈希和盐值
    password_hash, salt = generate_password_hash(password)
    
    # 生成SQL插入语句
    sql = f"""
-- 创建用户账号
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
    '{name}',
    '{email}',
    '{avatar}',
    '{password_hash}',
    '{salt}',
    CURRENT_TIMESTAMP,
    '127.0.0.1',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
"""
    return sql, password_hash, salt

def create_user_interactive():
    """交互式创建用户"""
    print("🚀 LLMOps 用户创建工具")
    print("=" * 50)
    
    # 获取用户输入
    name = input("请输入用户名: ").strip()
    if not name:
        print("❌ 用户名不能为空")
        return
    
    email = input("请输入邮箱: ").strip()
    if not email:
        print("❌ 邮箱不能为空")
        return
    
    password = input("请输入密码: ").strip()
    if not password:
        print("❌ 密码不能为空")
        return
    
    avatar = input("请输入头像URL (可选，直接回车跳过): ").strip()
    
    print("\n📋 用户信息确认:")
    print(f"用户名: {name}")
    print(f"邮箱: {email}")
    print(f"密码: {'*' * len(password)}")
    print(f"头像: {avatar if avatar else '(无)'}")
    
    confirm = input("\n确认创建用户? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ 用户创建已取消")
        return
    
    # 生成SQL语句
    sql, password_hash, salt = create_user_sql(name, email, password, avatar)
    
    print("\n✅ SQL语句已生成!")
    print("=" * 50)
    print(sql)
    print("=" * 50)
    
    # 保存到文件
    sql_file = f"create_user_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(f"-- 创建用户: {name} ({email})\n")
        f.write(f"-- 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- 密码哈希: {password_hash}\n")
        f.write(f"-- 盐值: {salt}\n\n")
        f.write(sql)
    
    print(f"📁 SQL语句已保存到文件: {sql_file}")
    print("\n🔧 执行方法:")
    print("1. 连接到 PostgreSQL 数据库:")
    print("   psql -U postgres -h localhost -d llmops")
    print("2. 执行SQL文件:")
    print(f"   \\i {sql_file}")
    print("3. 或者直接复制上面的SQL语句执行")
    
    print("\n🎉 用户创建完成后，您可以使用以下信息登录:")
    print(f"邮箱: {email}")
    print(f"密码: {password}")

def create_default_admin():
    """创建默认管理员账号"""
    print("🔧 创建默认管理员账号...")
    
    name = "admin"
    email = "admin@llmops.local"
    password = "admin123"
    avatar = ""
    
    sql, password_hash, salt = create_user_sql(name, email, password, avatar)
    
    print("✅ 默认管理员账号SQL:")
    print("=" * 50)
    print(sql)
    print("=" * 50)
    
    # 保存到文件
    sql_file = "create_admin_user.sql"
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write("-- 默认管理员账号\n")
        f.write(f"-- 用户名: {name}\n")
        f.write(f"-- 邮箱: {email}\n")
        f.write(f"-- 密码: {password}\n")
        f.write(f"-- 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(sql)
    
    print(f"📁 SQL语句已保存到文件: {sql_file}")
    print("\n🎉 默认管理员账号信息:")
    print(f"邮箱: {email}")
    print(f"密码: {password}")

if __name__ == "__main__":
    # 加载环境变量
    dotenv.load_dotenv()
    
    print("请选择操作:")
    print("1. 交互式创建用户")
    print("2. 创建默认管理员账号")
    
    choice = input("请输入选择 (1/2): ").strip()
    
    if choice == "1":
        create_user_interactive()
    elif choice == "2":
        create_default_admin()
    else:
        print("❌ 无效选择")
