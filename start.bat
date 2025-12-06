@echo off
echo ========================================
echo       启动 LLMOps 服务
echo ========================================

echo.
echo 1. 启动 Docker 服务...
cd docker\docker
docker-compose up -d

if %errorlevel% neq 0 (
    echo ❌ Docker 服务启动失败！
    pause
    exit /b 1
)

echo ✅ Docker 服务启动成功！

echo.
echo 2. 等待服务完全启动...
timeout /t 15 /nobreak

echo.
echo 3. 验证 Weaviate 服务...
docker logs llmops-weaviate --tail 5

echo.
echo 4. 启动后端应用...
cd ..\..\imooc-llmops-api\imooc-llmops-api-master

echo 激活虚拟环境...
call .venv\Scripts\Activate.bat

echo 启动 Flask 应用...
python -m app.http.app

pause
