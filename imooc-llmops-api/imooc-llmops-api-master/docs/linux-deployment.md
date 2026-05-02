# Linux 部署补充说明

## 依赖入口

- Linux 容器默认使用 `requirements-linux.txt`
- `requirements-linux.txt` 复用 `requirements.txt`
- Windows 专属依赖通过环境标记自动跳过

## 当前 Docker 运行时关键点

- Python 基础镜像：`python:3.11-slim`
- 安装了这些 Linux 运行库：
  - `libpq-dev`
  - `libmagic1`
  - `libmagic-dev`
  - `poppler-utils`
  - `libglib2.0-0`
  - `libgomp1`
- pip 安装优先走 wheel，减少源代码编译失败

## 镜像构建建议

首次构建：

```bash
docker compose -f docker-compose.prod.yml build --no-cache llmops-api celery-worker
docker compose -f docker-compose.prod.yml up -d
```

## 环境变量建议

- 首次部署建议 `TRANSFORMERS_OFFLINE=0`
- 如果模型缓存已经预热完成，再按需切回 `1`
- 如果服务器无法访问外网模型源，请先准备好本地缓存

## 额外提醒

当前通用上传链路默认依赖 COS。
如果你还没有配置 `COS_*`，建议先以：

- 平台管理
- Agent/WebApp 对话

为主验证部署是否成功，再决定是否补齐对象存储配置。
