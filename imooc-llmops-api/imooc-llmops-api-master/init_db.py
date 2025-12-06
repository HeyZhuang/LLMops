#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于本地开发环境的数据库初始化
"""
import os
import sys
import dotenv
from flask_migrate import upgrade

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """初始化数据库"""
    print("🚀 开始初始化 LLMOps 数据库...")
    
    # 1. 加载环境变量
    print("1. 加载环境变量...")
    dotenv.load_dotenv()
    
    # 2. 检查数据库连接配置
    db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
    if not db_uri:
        print("❌ 错误: 未找到数据库连接配置 SQLALCHEMY_DATABASE_URI")
        print("请检查 .env 文件中的数据库配置")
        sys.exit(1)
    
    print(f"   数据库连接: {db_uri}")
    
    # 3. 设置Flask应用环境变量和编码
    os.environ['FLASK_APP'] = 'app.http.app:app'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        # 4. 导入Flask应用
        print("2. 初始化Flask应用...")
        from app.http.app import app
        
        # 5. 执行数据库迁移
        print("3. 执行数据库迁移...")
        with app.app_context():
            # 设置迁移目录的编码
            migration_dir = os.path.join(os.getcwd(), 'internal', 'migration')
            upgrade(directory=migration_dir)
        
        print("✅ 数据库初始化完成！")
        print("\n📋 已创建的主要数据表:")
        print("   - account (用户账号表)")
        print("   - account_oauth (第三方授权表)")
        print("   - app (AI应用表)")
        print("   - app_config (应用配置表)")
        print("   - app_config_version (应用配置版本表)")
        print("   - app_dataset_join (应用知识库关联表)")
        print("   - conversation (对话会话表)")
        print("   - message (对话消息表)")
        print("   - message_agent_thought (智能体推理表)")
        print("   - dataset (知识库表)")
        print("   - document (文档表)")
        print("   - segment (文档片段表)")
        print("   - keyword_table (关键词表)")
        print("   - dataset_query (知识库查询表)")
        print("   - process_rule (文档处理规则表)")
        print("   - api_key (API密钥表)")
        print("   - api_tool (API工具表)")
        print("   - end_user (终端用户表)")
        print("   - upload_file (文件上传表)")
        print("   - workflow (工作流表)")
        print("\n🎉 现在可以启动应用了!")
        
    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        print("请确保已安装所有依赖包: pip install -r requirements.txt")
        sys.exit(1)
    except UnicodeDecodeError as e:
        print(f"❌ 编码错误: {str(e)}")
        print("\n🔧 编码问题解决方案:")
        print("1. 检查迁移文件是否包含非UTF-8字符")
        print("2. 尝试重新生成迁移文件")
        print("3. 或者使用 alembic 直接执行迁移")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        print("\n🔧 故障排除建议:")
        print("1. 确保 PostgreSQL 数据库服务正在运行")
        print("2. 确保数据库 'llmops' 已创建")
        print("3. 确保已启用 uuid-ossp 扩展")
        print("4. 检查数据库连接配置是否正确")
        print("5. 检查迁移文件编码是否正确")
        sys.exit(1)

if __name__ == "__main__":
    init_database()
