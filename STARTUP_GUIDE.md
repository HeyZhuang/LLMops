# LLMOps 平台启动指南

## 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| **Python** | **3.11** | Dockerfile 明确指定 `python:3.11-slim`，推荐使用 3.11 |
| Node.js | 16+（推荐 20） | Dockerfile 使用 `node:20` |
| PostgreSQL | 12+（推荐 15） | 启动脚本检查 PostgreSQL 15 |
| Redis | 6+ | 缓存 + Celery 消息队列 |
| Docker | 20.10+ | 用于运行 Weaviate 向量数据库 |

> **关于 Python 版本**：虽然 README 写的是 "3.8+"，但后端 Dockerfile 使用的是 `python:3.11-slim`，依赖库（Flask 3.0.2、LangChain 0.2.16、pandas 2.2.2、torch 2.4.1 等）也都要求较新版本。**建议使用 Python 3.11**，这是项目的实际目标运行版本。

---

## 方式一：本地开发（推荐）

### 1. 启动基础服务

确保本地已安装并运行 PostgreSQL 和 Redis，然后启动 Weaviate：

```bash
cd docker/docker
docker-compose -f docker-compose-weaviate-only.yaml up -d
```

### 2. 后端配置与启动

```bash
cd imooc-llmops-api/imooc-llmops-api-master

# 创建虚拟环境（Python 3.11）
python -m venv .venv

# 激活虚拟环境
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（从模板复制后编辑）
cp .env.example .env
# 编辑 .env，填写以下关键配置：
#   SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost:5432/llmops
#   REDIS_HOST=localhost
#   REDIS_PORT=6379
#   WEAVIATE_HOST=localhost
#   WEAVIATE_PORT=8080
#   JWT_SECRET_KEY=your_secret
#   OPENAI_API_KEY=your_key（及其他 LLM 提供商密钥）

# 初始化数据库
python init_db.py

# 创建用户
python create_user.py

# 启动 Flask 后端（端口 5000）
python -m app.http.app
```

### 3. 启动 Celery 异步任务（另开终端）

```bash
cd imooc-llmops-api/imooc-llmops-api-master

# 激活虚拟环境后：
# Windows:
celery -A app.celery worker --loglevel=info --pool=solo
# Linux/Mac:
celery -A app.celery worker --loglevel=info
```

### 4. 前端配置与启动（另开终端）

```bash
cd imooc-llmops-ui/imooc-llmops-ui-master

# 安装依赖（项目中有 yarn.lock，推荐用 yarn）
yarn install
# 或
npm install

# 启动开发服务器（端口 5173）
npm run dev
```

### 5. 验证服务

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:5000 |
| Weaviate | http://localhost:8080 |

---

## 方式二：一键脚本启动（Windows）

项目根目录提供了批处理脚本：

```bash
# 本地开发模式（本地 PG + Redis，Docker 仅 Weaviate）
start-local.bat

# 停止
stop-local.bat
```

---

## 方式三：完整 Docker 部署

```bash
cd docker/docker

# 启动完整服务栈（Weaviate + API + UI）
docker-compose up -d
```

此模式下后端 API 端口为 **8000**（非 5000）。

---

## 常见问题

1. **数据库迁移**：如果表结构有更新，运行 `python migrate_db.py`
2. **Windows 上 Celery 报错**：必须加 `--pool=solo` 参数
3. **Weaviate 版本**：项目使用 `1.23.7`，docker-compose 文件中已锁定
4. **LLM 提供商**：支持 OpenAI / Moonshot / 通义 / 文心 / Ollama，在 `.env` 中配置对应密钥即可
