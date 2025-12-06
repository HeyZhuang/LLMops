@echo off
echo ========================================
echo       停止 LLMOps 服务
echo ========================================

echo.
echo 1. 停止 Docker 服务...
cd docker\docker
docker-compose down

if %errorlevel% neq 0 (
    echo ❌ Docker 服务停止失败！
    pause
    exit /b 1
)

echo ✅ Docker 服务已停止！

echo.
echo 2. 清理 Docker 资源（可选）...
echo 是否要清理未使用的 Docker 资源？ (y/N)
set /p cleanup="请输入选择: "

if /i "%cleanup%"=="y" (
    echo 清理 Docker 资源...
    docker system prune -f
    echo ✅ Docker 资源清理完成！
) else (
    echo 跳过 Docker 资源清理
)

echo.
echo ========================================
echo       所有服务已停止
echo ========================================

pause
