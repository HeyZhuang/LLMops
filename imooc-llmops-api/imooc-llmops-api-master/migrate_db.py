#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本
用于初始化和升级数据库表结构
"""
import os
import sys
import dotenv
from flask_migrate import upgrade

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
dotenv.load_dotenv()

# 导入Flask应用
from app.http.app import app

def migrate_database():
    """执行数据库迁移"""
    with app.app_context():
        try:
            print("开始执行数据库迁移...")
            
            # 执行数据库升级
            upgrade(directory='internal/migration')
            
            print("✅ 数据库迁移完成！")
            print("所有表结构已成功创建或更新。")
            
        except Exception as e:
            print(f"❌ 数据库迁移失败: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    migrate_database()
