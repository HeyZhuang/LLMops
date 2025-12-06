@echo off
echo ========================================
echo    LLMOps 本地开发环境启动脚本
echo    使用本地 PostgreSQL 和 Redis
echo    Docker 仅运行 Weaviate 向量数据库
echo ========================================
echo.

echo 1. 检查本地服务状态...
echo.

echo 检查 PostgreSQL 服务...
sc query postgresql-x64-15 >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ PostgreSQL 服务已安装
) else (
    echo ❌ 未找到 PostgreSQL 服务，请确保已安装并启动 PostgreSQL
    pause
    exit /b 1
)

echo 检查 Redis 服务...
sc query Redis >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Redis 服务已安装
) else (
    echo ⚠️  未找到 Redis 服务，请确保已安装并启动 Redis
)

echo.
echo 2. 启动 Weaviate 向量数据库 (Docker)...
cd docker\docker
docker-compose -f docker-compose-local.yaml up -d

echo.
echo 3. 等待 Weaviate 启动完成...
timeout /t 10

echo.
echo 4. 验证 Weaviate 服务...
curl -s http://localhost:8080/v1/meta >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Weaviate 服务启动成功
) else (
    echo ⚠️  Weaviate 服务可能还在启动中，请稍后手动验证
)

echo.
echo 5. 准备启动后端应用...
cd ..\..\imooc-llmops-api\imooc-llmops-api-master

echo.
echo 检查环境配置文件...
if exist .env (
    echo ✅ 找到 .env 配置文件
) else (
    echo ⚠️  未找到 .env 文件，正在从 .env.local 复制...
    copy .env.local .env
    echo ✅ 已创建 .env 文件，请检查并修改数据库连接配置
    echo.
    echo 重要提醒：
    echo - 请修改 .env 文件中的 PostgreSQL 密码
    echo - 请设置您的 OpenAI API Key
    echo.
    pause
)

echo.
echo 6. 初始化数据库表结构...
python init_db.py
if %errorlevel% neq 0 (
    echo ❌ 数据库初始化失败，请检查配置
    pause
    exit /b 1
)

echo.
echo 7. 启动后端应用...
echo 应用将在 http://0.0.0.0:5000 启动
echo 按 Ctrl+C 停止应用
echo.
python -m app.http.app

pause
