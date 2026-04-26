FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 默认使用国内 APT 镜像（可通过构建参数覆盖，例如：--build-arg APT_MIRROR=mirrors.tuna.tsinghua.edu.cn）
ARG APT_MIRROR=mirrors.aliyun.com

# 【优化 1：替换 Debian 系统源为阿里云镜像】
# 忽略报错以兼容不同版本的 Debian 配置文件格式
RUN sed -i "s/deb.debian.org/${APT_MIRROR}/g" /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && sed -i "s/security.debian.org/${APT_MIRROR}/g" /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && sed -i "s/deb.debian.org/${APT_MIRROR}/g" /etc/apt/sources.list 2>/dev/null || true \
    && sed -i "s/security.debian.org/${APT_MIRROR}/g" /etc/apt/sources.list 2>/dev/null || true \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 【优化 2：使用清华源加速安装 Python 依赖】
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "app.http.app:app"]
