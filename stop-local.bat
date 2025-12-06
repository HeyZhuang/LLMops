@echo off
echo ========================================
echo    LLMOps 本地开发环境停止脚本
echo ========================================
echo.

echo 1. 停止 Weaviate 向量数据库容器...
cd docker\docker
docker-compose -f docker-compose-local.yaml down

echo.
echo 2. 清理 Docker 资源...
docker system prune -f

echo.
echo ✅ 本地开发环境已停止
echo.
echo 注意：本地的 PostgreSQL 和 Redis 服务仍在运行
echo 如需停止，请手动停止相应服务：
echo - PostgreSQL: net stop postgresql-x64-15
echo - Redis: net stop Redis
echo.

pause
