# Docker 部署说明

本项目已补充适合单台云服务器的生产部署文件，适用于 2 核 4G 的轻量场景。

## 1. 服务器准备

推荐系统：Ubuntu 22.04。

安装 Docker：

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git curl
sudo systemctl enable docker
sudo systemctl start docker
```

建议开启 2G swap：

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 2. 上传代码

```bash
cd /opt
git clone <your-repo-url> llmops
cd /opt/llmops
```

## 3. 配置后端环境变量

复制模板并编辑：

```bash
cp imooc-llmops-api/imooc-llmops-api-master/.env.prod.example imooc-llmops-api/imooc-llmops-api-master/.env
```

重点修改：

- `JWT_SECRET_KEY`
- `OPENAI_API_KEY` 和其他模型密钥
- `POSTGRES_PASSWORD`
- `GITHUB_REDIRECT_URI`
- 对象存储相关配置

如果你修改了数据库密码，记得同时更新：

- `imooc-llmops-api/imooc-llmops-api-master/.env`
- 根目录 `.env` 中的 `POSTGRES_PASSWORD`

## 4. 可选：创建 Compose 根环境文件

为了给 `docker-compose.prod.yml` 传递数据库密码，推荐在仓库根目录创建 `.env`：

```env
POSTGRES_PASSWORD=ChangeMe123!
```

## 5. 启动服务

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

查看状态：

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f llmops-api
```

## 6. 初始化数据库

首次部署执行：

```bash
docker compose -f docker-compose.prod.yml exec llmops-api python init_db.py
docker compose -f docker-compose.prod.yml exec llmops-api python create_user.py
```

如有表结构变更：

```bash
docker compose -f docker-compose.prod.yml exec llmops-api python migrate_db.py
```

## 7. 访问地址

- 前端：`http://服务器IP`
- API：通过 Nginx 反代走 `/api`

## 8. 更新部署

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## 9. 文件说明

- `docker-compose.prod.yml`：生产编排
- `deploy/nginx.conf`：Nginx 反向代理
- `imooc-llmops-api/imooc-llmops-api-master/.env.prod.example`：后端生产环境变量模板

## 10. 轻量服务器建议

- 当前编排已将 Gunicorn 调整为 `2 workers + 2 threads`
- Celery 并发设置为 `1`
- 不建议一次性导入大量大文件
- 建议优先通过域名和 HTTPS 对外提供访问
