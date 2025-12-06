-- LLMOps 项目数据库初始化脚本
-- 注意：请先确保已安装 PostgreSQL 数据库

-- 1. 创建数据库（如果不存在）
-- 在 PostgreSQL 命令行或 pgAdmin 中执行：
-- CREATE DATABASE llmops;

-- 2. 连接到数据库后，启用 UUID 扩展（必须执行）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 注意：表结构将通过 Flask-Migrate 自动创建，不需要手动执行建表语句
-- 执行完上述扩展创建后，请运行以下 Python 命令来创建表：
-- flask db upgrade



