@echo off
setlocal
set "ROOT=%~dp0"
set "DOCKER_DIR=%ROOT%docker\docker"
set "API_DIR=%ROOT%imooc-llmops-api\imooc-llmops-api-master"
set "UI_DIR=%ROOT%imooc-llmops-ui\imooc-llmops-ui-master"

chcp 65001 >nul 2>&1

echo ========================================
echo          Starting LLMOps Services
echo ========================================

echo.
echo 1. Starting Docker vector database...
pushd "%DOCKER_DIR%"
docker-compose -f docker-compose-local.yaml up -d
if %errorlevel% neq 0 (
    echo Docker startup failed.
    popd
    pause
    exit /b 1
)
popd
echo Docker vector database started.

echo.
echo 2. Waiting for Weaviate to warm up...
timeout /t 10 /nobreak >nul

echo.
echo 3. Starting backend...
if not exist "%API_DIR%\.env" (
    copy /y "%API_DIR%\.env.local" "%API_DIR%\.env" >nul
)
start "LLMOps - Backend" cmd /k "cd /d ""%API_DIR%"" && powershell -NoProfile -ExecutionPolicy Bypass -File ""%ROOT%start-local-safe.ps1"""

echo 4. Starting Celery worker...
start "LLMOps - Celery" cmd /k "powershell -NoProfile -ExecutionPolicy Bypass -File ""%ROOT%start-celery-safe.ps1"""

echo 5. Starting frontend...
start "LLMOps - Frontend" cmd /k "cd /d ""%UI_DIR%"" && npm run dev"

echo.
echo All services are launching in separate windows.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:5173
echo Weaviate: http://localhost:8080
echo.

endlocal
