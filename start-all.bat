@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

:: =============================================
::   LLMOps 一键启动脚本 (全服务)
::   启动: Weaviate + Flask后端 + Celery + Vue前端
:: =============================================

set "ROOT_DIR=%~dp0"
set "API_DIR=%ROOT_DIR%imooc-llmops-api\imooc-llmops-api-master"
set "UI_DIR=%ROOT_DIR%imooc-llmops-ui\imooc-llmops-ui-master"
set "DOCKER_DIR=%ROOT_DIR%docker\docker"
set "VENV_DIR=%API_DIR%\.venv"

set ERRORS=0

echo.
echo  ============================================
echo       LLMOps 一键启动脚本
echo  ============================================
echo.
echo  [1] Weaviate 向量数据库 (Docker)
echo  [2] Flask 后端 API 服务
echo  [3] Celery 异步任务 Worker
echo  [4] Vue 3 前端开发服务器
echo  ============================================
echo.

:: ------------------------------------------
:: 阶段0: 环境检查
:: ------------------------------------------
echo  [检查] 验证环境依赖...
echo.

:: 检查 Docker
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo  [X] Docker 未安装或不在 PATH 中
    set /a ERRORS+=1
) else (
    docker info >nul 2>&1
    if !errorlevel! neq 0 (
        echo  [X] Docker Desktop 未运行，请先启动 Docker Desktop
        set /a ERRORS+=1
    ) else (
        echo  [OK] Docker 已就绪
    )
)

:: 检查 Python 虚拟环境
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo  [OK] Python 虚拟环境已就绪
) else (
    echo  [X] 未找到 Python 虚拟环境: %VENV_DIR%
    set /a ERRORS+=1
)

:: 检查 Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo  [X] Node.js 未安装或不在 PATH 中
    set /a ERRORS+=1
) else (
    echo  [OK] Node.js 已就绪
)

:: 检查 PostgreSQL 服务
sc query postgresql-x64-15 >nul 2>&1
if %errorlevel% == 0 (
    echo  [OK] PostgreSQL 服务已安装
) else (
    sc query postgresql-x64-16 >nul 2>&1
    if !errorlevel! == 0 (
        echo  [OK] PostgreSQL 服务已安装
    ) else (
        echo  [!] 未检测到 PostgreSQL 服务，请确认已启动
    )
)

:: 检查 Redis 服务
sc query Redis >nul 2>&1
if %errorlevel% == 0 (
    echo  [OK] Redis 服务已安装
) else (
    echo  [!] 未检测到 Redis 服务，请确认已启动
)

:: 检查后端 .env 文件
if exist "%API_DIR%\.env" (
    echo  [OK] 后端 .env 配置文件已就绪
) else (
    echo  [!] 未找到 .env 文件，将尝试从 .env.local 复制
    if exist "%API_DIR%\.env.local" (
        copy "%API_DIR%\.env.local" "%API_DIR%\.env" >nul
        echo  [OK] 已从 .env.local 复制 .env，请检查配置
    ) else if exist "%API_DIR%\.env.example" (
        copy "%API_DIR%\.env.example" "%API_DIR%\.env" >nul
        echo  [OK] 已从 .env.example 复制 .env，请检查配置
    ) else (
        echo  [X] 无法创建 .env 文件，请手动配置
        set /a ERRORS+=1
    )
)

echo.

:: 如果存在致命错误则退出
if %ERRORS% gtr 0 (
    echo  发现 %ERRORS% 个环境问题，请先修复后再启动。
    echo.
    pause
    exit /b 1
)

echo  环境检查通过！开始启动服务...
echo.

:: ------------------------------------------
:: 阶段1: 启动 Weaviate (Docker)
:: ------------------------------------------
echo  [1/4] 启动 Weaviate 向量数据库...

:: 检查 Weaviate 是否已在运行
docker ps --filter "name=llmops-weaviate" --format "{{.Names}}" 2>nul | findstr /i "llmops-weaviate" >nul 2>&1
if %errorlevel% == 0 (
    echo         Weaviate 已在运行，跳过启动
) else (
    cd /d "%DOCKER_DIR%"
    docker-compose -f docker-compose-local.yaml up -d
    if !errorlevel! neq 0 (
        echo  [X] Weaviate 启动失败！
        pause
        exit /b 1
    )
    echo         Weaviate 启动中...
)

:: ------------------------------------------
:: 阶段2: 等待 Weaviate 就绪
:: ------------------------------------------
echo  [....] 等待 Weaviate 就绪...
set WEAVIATE_READY=0
for /L %%i in (1,1,15) do (
    if !WEAVIATE_READY! == 0 (
        curl -s http://localhost:8080/v1/meta >nul 2>&1
        if !errorlevel! == 0 (
            set WEAVIATE_READY=1
            echo         Weaviate 已就绪
        ) else (
            timeout /t 2 /nobreak >nul
        )
    )
)
if %WEAVIATE_READY% == 0 (
    echo  [!] Weaviate 可能仍在启动中，继续启动其他服务...
)

echo.

:: ------------------------------------------
:: 阶段3: 启动 Flask 后端
:: ------------------------------------------
echo  [2/4] 启动 Flask 后端 API 服务...

start "LLMOps - Flask Backend" cmd /k "title LLMOps - Flask Backend (port 5000) && cd /d "%API_DIR%" && call .venv\Scripts\activate.bat && echo. && echo  Flask 后端正在启动... && echo  地址: http://localhost:5000 && echo  按 Ctrl+C 停止 && echo. && python -m app.http.app"

:: 给后端一点启动时间
timeout /t 3 /nobreak >nul
echo         Flask 后端已在新窗口中启动

echo.

:: ------------------------------------------
:: 阶段4: 启动 Celery Worker
:: ------------------------------------------
echo  [3/4] 启动 Celery 异步任务 Worker...

start "LLMOps - Celery Worker" cmd /k "title LLMOps - Celery Worker && cd /d "%API_DIR%" && call .venv\Scripts\activate.bat && echo. && echo  Celery Worker 正在启动... && echo  按 Ctrl+C 停止 && echo. && celery -A app.http.app:celery worker --loglevel=info --pool=solo"

echo         Celery Worker 已在新窗口中启动

echo.

:: ------------------------------------------
:: 阶段5: 启动 Vue 前端
:: ------------------------------------------
echo  [4/4] 启动 Vue 3 前端开发服务器...

start "LLMOps - Vue Frontend" cmd /k "title LLMOps - Vue Frontend (port 5173) && cd /d "%UI_DIR%" && echo. && echo  Vue 前端正在启动... && echo  地址: http://localhost:5173 && echo  按 Ctrl+C 停止 && echo. && npm run dev"

echo         Vue 前端已在新窗口中启动

echo.

:: ------------------------------------------
:: 完成
:: ------------------------------------------
echo  ============================================
echo       所有服务已启动！
echo  ============================================
echo.
echo   Weaviate:  http://localhost:8080
echo   后端 API:  http://localhost:5000
echo   前端页面:  http://localhost:5173
echo.
echo  每个服务在独立窗口中运行，关闭窗口即停止对应服务。
echo  或运行 stop-all.bat 一键停止所有服务。
echo.
echo  ============================================
echo.

:: 询问是否打开浏览器
set /p OPEN_BROWSER="  是否打开浏览器访问前端？(Y/n): "
if /i "%OPEN_BROWSER%" neq "n" (
    timeout /t 5 /nobreak >nul
    start http://localhost:5173
)

endlocal
