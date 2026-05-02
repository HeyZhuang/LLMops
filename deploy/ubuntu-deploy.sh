#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.prod.yml"
API_ENV_FILE="${ROOT_DIR}/imooc-llmops-api/imooc-llmops-api-master/.env"
DOCKER_ENV_FILE="${ROOT_DIR}/.env"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not installed."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose plugin is not available."
  exit 1
fi

if [[ ! -f "${DOCKER_ENV_FILE}" ]]; then
  echo "Missing ${DOCKER_ENV_FILE}. Create it from .env.docker.example first."
  exit 1
fi

if [[ ! -f "${API_ENV_FILE}" ]]; then
  echo "Missing ${API_ENV_FILE}. Create it from .env.prod.example first."
  exit 1
fi

cd "${ROOT_DIR}"

echo "[1/4] Build and start containers..."
docker compose -f "${COMPOSE_FILE}" up -d --build

echo "[2/4] Initialize database schema..."
docker compose -f "${COMPOSE_FILE}" exec -T llmops-api python init_db.py

echo "[3/4] Bootstrap admin account..."
docker compose -f "${COMPOSE_FILE}" exec -T llmops-api python bootstrap_admin.py

echo "[4/4] Current container status:"
docker compose -f "${COMPOSE_FILE}" ps

echo
echo "Deployment completed."
echo "Open: http://<your-server-ip>/"
echo "WebApp route: http://<your-server-ip>/web-apps/<token>"
