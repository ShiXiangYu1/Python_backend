FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置Python环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 创建非root用户
RUN adduser --disabled-password --gecos "" appuser
RUN mkdir -p /app/uploads/models && chown -R appuser:appuser /app

# 复制项目文件
COPY . .

# 设置入口点脚本权限
RUN chmod +x scripts/docker-entrypoint.sh
RUN chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8000

# 设置入口点
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"] 