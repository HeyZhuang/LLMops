#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/3/29 15:18
@Author  : ccckz@protonmail.com
@File    : app.py
"""
import os
import dotenv
from flask_login import LoginManager
from flask_migrate import Migrate

from config import Config
from internal.middleware import Middleware
from internal.router import Router
from internal.server import Http
from pkg.sqlalchemy import SQLAlchemy
from .module import injector

# 1.将env加载到环境变量中
dotenv.load_dotenv()

# 将poppler加入PATH（Windows PDF解析依赖）
poppler_path = os.getenv("POPPLER_PATH")
if poppler_path and poppler_path not in os.environ.get("PATH", ""):
    os.environ["PATH"] = poppler_path + os.pathsep + os.environ.get("PATH", "")

# 2.构建LLMOps项目配置
conf = Config()

app = Http(
    __name__,
    conf=conf,
    db=injector.get(SQLAlchemy),
    migrate=injector.get(Migrate),
    login_manager=injector.get(LoginManager),
    middleware=injector.get(Middleware),
    router=injector.get(Router),
)

celery = app.extensions["celery"]

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1"), host='0.0.0.0', port=5000)
