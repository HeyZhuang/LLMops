#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的数据库初始化脚本
使用 Alembic 直接执行迁移，避免编码问题
"""
import os
import sys
import subprocess
import dotenv

def init_database_simple():
    """简化的数据库初始化"""
    print("🚀 开始初始化 LLMOps 数据库 (简化版)...")
    
    # 1. 加载环境变量
    print("1. 加载环境变量...")
    dotenv.load_dotenv()
    
    # 2. 检查数据库连接配置
    db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
    if not db_uri:
        print("❌ 错误: 未找到数据库连接配置 SQLALCHEMY_DATABASE_URI")
        print("请检查 .env 文件中的数据库配置")
        return False
    
    print(f"   数据库连接: {db_uri}")
    
    # 3. 设置环境变量
    os.environ['FLASK_APP'] = 'app.http.app:app'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        # 4. 使用 Alembic 直接执行迁移
        print("2. 使用 Alembic 执行数据库迁移...")
        
        # 切换到迁移目录
        migration_dir = os.path.join(os.getcwd(), 'internal', 'migration')
        
        # 执行 alembic upgrade head
        cmd = [sys.executable, '-m', 'alembic', '-c', 'alembic.ini', 'upgrade', 'head']
        
        print(f"   执行命令: {' '.join(cmd)}")
        print(f"   工作目录: {migration_dir}")
        
        result = subprocess.run(
            cmd,
            cwd=migration_dir,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✅ 数据库迁移执行成功！")
            if result.stdout:
                print("输出:", result.stdout)
        else:
            print("❌ 数据库迁移执行失败！")
            if result.stderr:
                print("错误:", result.stderr)
            if result.stdout:
                print("输出:", result.stdout)
            return False
        
        print("\n📋 数据库初始化完成！")
        print("主要数据表已创建，包括:")
        print("   - 用户管理表 (account, account_oauth)")
        print("   - 应用管理表 (app, app_config, app_config_version)")
        print("   - 对话管理表 (conversation, message, message_agent_thought)")
        print("   - 知识库表 (dataset, document, segment)")
        print("   - 系统功能表 (api_key, upload_file, workflow)")
        print("\n🎉 现在可以启动应用了!")
        return True
        
    except FileNotFoundError:
        print("❌ 未找到 alembic 命令")
        print("请确保已安装 alembic: pip install alembic")
        return False
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        return False

def test_database_connection():
    """测试数据库连接"""
    print("\n🔍 测试数据库连接...")
    try:
        import psycopg2
        
        db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
        if not db_uri:
            print("❌ 未找到数据库连接配置")
            return False
        
        # 解析数据库连接字符串
        # postgresql://postgres:root@localhost:5432/llmops
        parts = db_uri.replace('postgresql://', '').split('@')
        user_pass = parts[0].split(':')
        host_db = parts[1].split('/')
        host_port = host_db[0].split(':')
        
        conn = psycopg2.connect(
            host=host_port[0],
            port=int(host_port[1]) if len(host_port) > 1 else 5432,
            database=host_db[1],
            user=user_pass[0],
            password=user_pass[1]
        )
        conn.close()
        print("✅ 数据库连接测试成功！")
        return True
        
    except ImportError:
        print("❌ 未安装 psycopg2，无法测试连接")
        print("请安装: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {str(e)}")
        print("\n🔧 请检查:")
        print("1. PostgreSQL 服务是否正在运行")
        print("2. 数据库 'llmops' 是否已创建")
        print("3. 用户名和密码是否正确")
        return False

if __name__ == "__main__":
    # 测试数据库连接
    if test_database_connection():
        # 初始化数据库
        success = init_database_simple()
        if not success:
            print("\n💡 如果遇到编码问题，请尝试:")
            print("1. 在 PowerShell 中设置编码: chcp 65001")
            print("2. 或者手动执行迁移命令:")
            print("   cd internal/migration")
            print("   python -m alembic upgrade head")
            sys.exit(1)
    else:
        sys.exit(1)
