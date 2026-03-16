@echo off
chcp 65001 >nul 2>&1
setlocal

:: =============================================
::   LLMOps 一键停止脚本 (全服务)
:: =============================================

set "ROOT_DIR=%~dp0"
set "DOCKER_DIR=%ROOT_DIR%docker\docker"

echo.
echo  ============================================
echo       LLMOps 一键停止脚本
echo  ============================================
echo.

:: ------------------------------------------
:: 1. 停止 Flask 后端
:: ------------------------------------------
echo  [1/4] 停止 Flask 后端进程...
for /f "tokens=2" %%a in ('tasklist /fi "WINDOWTITLE eq LLMOps - Flask Backend*" /fo list 2^>nul ^| findstr "PID:"') do (
    taskkill /PID %%a /T /F >nul 2>&1
)
:: 也尝试通过端口关闭
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /T /F >nul 2>&1
)
echo         Flask 后端已停止

:: ------------------------------------------
:: 2. 停止 Celery Worker
:: ------------------------------------------
echo  [2/4] 停止 Celery Worker 进程...
for /f "tokens=2" %%a in ('tasklist /fi "WINDOWTITLE eq LLMOps - Celery Worker*" /fo list 2^>nul ^| findstr "PID:"') do (
    taskkill /PID %%a /T /F >nul 2>&1
)
:: 也尝试杀掉所有 celery 相关进程
taskkill /f /im celery.exe >nul 2>&1
echo         Celery Worker 已停止

:: ------------------------------------------
:: 3. 停止 Vue 前端
:: ------------------------------------------
echo  [3/4] 停止 Vue 前端进程...
for /f "tokens=2" %%a in ('tasklist /fi "WINDOWTITLE eq LLMOps - Vue Frontend*" /fo list 2^>nul ^| findstr "PID:"') do (
    taskkill /PID %%a /T /F >nul 2>&1
)
:: 也尝试通过端口关闭
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /T /F >nul 2>&1
)
echo         Vue 前端已停止

:: ------------------------------------------
:: 4. 停止 Weaviate (Docker)
:: ------------------------------------------
echo  [4/4] 停止 Weaviate 容器...
docker ps --filter "name=llmops-weaviate" --format "{{.Names}}" 2>nul | findstr /i "llmops-weaviate" >nul 2>&1
if %errorlevel% == 0 (
    cd /d "%DOCKER_DIR%"
    docker-compose -f docker-compose-local.yaml down
    echo         Weaviate 已停止
) else (
    echo         Weaviate 未在运行
)

echo.
echo  ============================================
echo       所有服务已停止！
echo  ============================================
echo.
echo  注意：PostgreSQL 和 Redis 为系统服务，未被停止。
echo  如需停止，请手动执行：
echo    net stop postgresql-x64-15
echo    net stop Redis
echo.

pause
endlocal
