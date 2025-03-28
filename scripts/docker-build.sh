#!/bin/bash

# 构建Docker镜像的脚本

set -e

echo "构建AI模型平台Docker镜像..."
docker build -t ai-model-platform:latest .

echo "镜像构建完成: ai-model-platform:latest"
echo "可以使用以下命令启动开发环境:"
echo "docker-compose up -d"
echo "或启动生产环境:"
echo "docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d" 