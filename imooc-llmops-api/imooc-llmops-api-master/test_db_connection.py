#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库连接测试脚本
验证后端是否能正确连接到您的PostgreSQL数据库
"""
import os
import sys
import dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """测试数据库连接"""
    print("🔍 测试 LLMOps 后端数据库连接...")
    print("=" * 60)
    
    # 1. 加载环境变量
    print("1. 加载环境变量...")
    dotenv.load_dotenv()
    
    # 2. 获取数据库连接配置
    db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
    if not db_uri:
        print("❌ 错误: 未找到数据库连接配置 SQLALCHEMY_DATABASE_URI")
        return False
    
    print(f"   数据库连接URI: {db_uri}")
    
    try:
        # 3. 创建数据库引擎
        print("2. 创建数据库连接...")
        engine = create_engine(
            db_uri,
            pool_size=int(os.getenv('SQLALCHEMY_POOL_SIZE', 30)),
            pool_recycle=int(os.getenv('SQLALCHEMY_POOL_RECYCLE', 3600)),
            echo=os.getenv('SQLALCHEMY_ECHO', 'True').lower() == 'true'
        )
        
        # 4. 测试连接
        print("3. 测试数据库连接...")
        with engine.connect() as connection:
            # 测试基本连接
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ 数据库连接成功!")
            print(f"   PostgreSQL 版本: {version}")
            
            # 5. 检查数据库和模式
            print("4. 检查数据库结构...")
            
            # 检查当前数据库
            result = connection.execute(text("SELECT current_database()"))
            current_db = result.fetchone()[0]
            print(f"   当前数据库: {current_db}")
            
            # 检查当前模式
            result = connection.execute(text("SELECT current_schema()"))
            current_schema = result.fetchone()[0]
            print(f"   当前模式: {current_schema}")
            
            # 6. 检查 account 表是否存在
            print("5. 检查数据表...")
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"   找到 {len(tables)} 个数据表:")
                for table in tables:
                    print(f"     - {table}")
                
                # 特别检查 account 表
                if 'account' in tables:
                    print("✅ account 表存在!")
                    
                    # 检查 account 表结构
                    result = connection.execute(text("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'account'
                        ORDER BY ordinal_position
                    """))
                    columns = result.fetchall()
                    
                    print("   account 表结构:")
                    for col in columns:
                        nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                        print(f"     - {col[0]}: {col[1]} ({nullable})")
                    
                    # 检查是否有用户数据
                    result = connection.execute(text("SELECT COUNT(*) FROM account"))
                    user_count = result.fetchone()[0]
                    print(f"   用户数量: {user_count}")
                    
                else:
                    print("⚠️  account 表不存在，需要运行数据库迁移")
            else:
                print("⚠️  未找到任何数据表，需要运行数据库迁移")
            
            # 7. 检查 UUID 扩展
            print("6. 检查 PostgreSQL 扩展...")
            result = connection.execute(text("""
                SELECT extname FROM pg_extension WHERE extname = 'uuid-ossp'
            """))
            uuid_ext = result.fetchone()
            
            if uuid_ext:
                print("✅ uuid-ossp 扩展已安装")
            else:
                print("⚠️  uuid-ossp 扩展未安装，可能需要手动安装")
                print("   执行: CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        
        print("\n🎉 数据库连接测试完成!")
        print("=" * 60)
        print("✅ 您的数据库层级路径完全正确:")
        print("   postgres@localhost -> llmops -> public -> account")
        print("✅ 后端应该能够正常识别并连接到您的数据库")
        
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        print("\n🔧 可能的解决方案:")
        print("1. 检查 PostgreSQL 服务是否正在运行")
        print("2. 检查数据库连接配置是否正确")
        print("3. 检查用户名和密码是否正确")
        print("4. 检查数据库 'llmops' 是否存在")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
        return False

def test_flask_app_connection():
    """测试 Flask 应用的数据库连接"""
    print("\n🚀 测试 Flask 应用数据库连接...")
    print("=" * 60)
    
    try:
        # 导入 Flask 应用
        from app.http.app import app
        
        with app.app_context():
            from internal.extension.database_extension import db
            
            # 测试数据库连接
            result = db.session.execute(text("SELECT 1"))
            print("✅ Flask 应用数据库连接成功!")
            
            # 测试模型导入
            from internal.model.account import Account
            
            # 查询用户数量
            user_count = db.session.query(Account).count()
            print(f"   通过 ORM 查询到 {user_count} 个用户")
            
            return True
            
    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Flask 应用连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 LLMOps 数据库连接测试工具")
    print("=" * 60)
    
    # 测试直接数据库连接
    db_success = test_database_connection()
    
    if db_success:
        # 测试 Flask 应用连接
        flask_success = test_flask_app_connection()
        
        if flask_success:
            print("\n🎉 所有测试通过!")
            print("您的数据库配置完全正确，后端可以正常运行!")
        else:
            print("\n⚠️  Flask 应用连接有问题，但数据库本身是正常的")
    else:
        print("\n❌ 数据库连接测试失败，请检查配置")
