#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/4/5 18:50
@Author  : ccckz@protonmail.com
@File    : default_config.py
"""
# 应用默认配置项
DEFAULT_CONFIG = {
    # wft配置
    "WTF_CSRF_ENABLED": "False",

    # SQLAlchemy数据库配置
    "SQLALCHEMY_DATABASE_URI": "",
    "SQLALCHEMY_POOL_SIZE": 30,
    "SQLALCHEMY_POOL_RECYCLE": 3600,
    "SQLALCHEMY_ECHO": "True",

    # Redis数据库配置
    "REDIS_HOST": "localhost",
    "REDIS_PORT": 6379,
    "REDIS_USERNAME": "",
    "REDIS_PASSWORD": "",
    "REDIS_DB": 0,
    "REDIS_USE_SSL": "False",

    # 邮件配置
    "SMTP_HOST": "",
    "SMTP_PORT": 587,
    "SMTP_USER": "",
    "SMTP_PASSWORD": "",
    "SMTP_USE_TLS": "True",
    "SMTP_USE_SSL": "False",
    "MAIL_FROM": "",

    # 注册验证码配置
    "REGISTER_CODE_EXPIRE_SECONDS": 300,
    "REGISTER_CODE_RESEND_SECONDS": 60,

    # Celery默认配置
    "CELERY_BROKER_DB": 1,
    "CELERY_RESULT_BACKEND_DB": 1,
    "CELERY_TASK_IGNORE_RESULT": "False",
    "CELERY_RESULT_EXPIRES": 3600,
    "CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP": "True",

    # 辅助Agent智能体应用id
    "ASSISTANT_AGENT_ID": "6774fcef-b594-8008-b30c-a05b8190afe6",
    "SHARED_MEDICAL_ACCOUNT_ID": "",
}
