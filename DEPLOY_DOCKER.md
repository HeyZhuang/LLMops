# Ubuntu 一次性部署指南

这套流程面向单台 Ubuntu 22.04 服务器，目标是尽量少改配置，直接把 `LLMOps` 跑起来。

## 部署前说明

- 当前生产编排文件是 `docker-compose.prod.yml`
- 对外入口是 `Nginx`，默认暴露 `80`
- 容器内会自动连接：
  - `postgres`
  - `redis`
  - `weaviate`
- 我已经把 `llmops-api` 和 `celery-worker` 的数据库、Redis、Weaviate 地址写回了 Compose，避免你手改多处配置时不一致

## 1. 安装 Docker

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git curl
sudo systemctl enable docker
sudo systemctl start docker
```

建议给轻量服务器加一点 swap：

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 2. 拉代码

```bash
cd /opt
git clone <your-repo-url> llmops
cd /opt/llmops
```

## 3. 准备配置文件

### 3.1 准备 Docker 根配置

```bash
cp .env.docker.example .env
```

至少修改：

- `POSTGRES_PASSWORD`
- `LLMOPS_ADMIN_PASSWORD`

如果你的服务器在中国大陆，构建镜像慢，再按需改：

- `APT_MIRROR`
- `PIP_INDEX_URL`
- `PIP_EXTRA_INDEX_URL`

### 3.2 准备后端业务配置

```bash
cp imooc-llmops-api/imooc-llmops-api-master/.env.prod.example \
   imooc-llmops-api/imooc-llmops-api-master/.env
```

至少修改这些项：

- `JWT_SECRET_KEY`
- `OPENAI_API_KEY` 或你实际使用的模型厂商密钥
- `GITHUB_REDIRECT_URI` 如果你要用 GitHub 登录

可选项：

- `COS_SECRET_ID`
- `COS_SECRET_KEY`
- `COS_REGION`
- `COS_BUCKET`
- `COS_DOMAIN`

说明：

- 现在 Compose 会覆盖容器里的 `SQLALCHEMY_DATABASE_URI`、`REDIS_HOST/PORT`、`WEAVIATE_HOST/PORT`
- 所以后端 `.env` 不需要再手动改数据库主机为 `postgres`
- 你只需要维护业务密钥和平台配置

## 4. 启动服务

### 4.1 一键方式

```bash
chmod +x deploy/ubuntu-deploy.sh
./deploy/ubuntu-deploy.sh
```

这个脚本会自动执行：

- `docker compose up -d --build`
- `python init_db.py`
- `python bootstrap_admin.py`

### 4.2 手动方式

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

查看状态：

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f llmops-api
```

## 5. 初始化数据库

首次部署执行：

```bash
docker compose -f docker-compose.prod.yml exec llmops-api python init_db.py
```

## 6. 初始化管理员账号

现在可以直接使用下面的命令把管理员写入数据库：

```bash
docker compose -f docker-compose.prod.yml exec llmops-api python bootstrap_admin.py
```

管理员账号来自根目录 `.env`：

- `LLMOPS_ADMIN_EMAIL`
- `LLMOPS_ADMIN_PASSWORD`

如果你之后想重置管理员密码，改完 `.env` 再执行一次同样命令即可。

## 7. 访问地址

- 平台首页：`http://你的服务器IP/`
- API 前缀：`http://你的服务器IP/api`

## 8. 后续更新

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

如果有数据库结构变更：

```bash
docker compose -f docker-compose.prod.yml exec llmops-api python migrate_db.py
```

## 9. 常见坑

### 9.1 Weaviate 无法连接

这套编排已经把 Weaviate 匿名访问打开了，否则当前后端代码默认无法携带鉴权头访问它。

### 9.2 上传文件/图标失败

当前项目的大部分通用上传逻辑仍依赖腾讯云 COS：

- 应用图标
- 普通文档上传
- 图片上传

如果你没有配置 `COS_*`，平台主体能启动，但上述上传能力会受限。

### 9.3 `/web-apps/:token` 体验链路

只要：

- 平台能正常登录
- 你发布了一个应用
- 拿到了该应用的 token

别人就可以直接访问：

```text
http://你的服务器IP/web-apps/<token>
```

## 10. 这次我帮你修正了什么

- 统一了 Compose 中 API/Celery 的数据库、Redis、Weaviate 连接配置
- 修正了 Weaviate 默认匿名访问配置，避免 RAG 容器内连不通
- 增加了 `backend_storage` 持久化卷，避免后端 `storage/` 在重建容器后丢失
- 增加了 `bootstrap_admin.py`，替代原来不能直接登录的管理员初始化脚本
- 增加了 `.env.docker.example`，把 Docker 级配置单独收口
