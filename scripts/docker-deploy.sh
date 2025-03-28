#!/bin/bash

# 部署Docker容器的脚本

set -e

# 检查环境参数
ENV=${1:-dev}

if [ "$ENV" = "prod" ]; then
    echo "部署生产环境..."
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
    
    # 确保必要的目录存在
    mkdir -p nginx/ssl nginx/logs
    
    echo "启动生产容器..."
    docker-compose $COMPOSE_FILES up -d
    
    echo "生产环境已启动"
    echo "请确保您已配置了正确的SSL证书和Nginx配置"
else
    echo "部署开发环境..."
    
    echo "启动开发容器..."
    docker-compose up -d
    
    echo "开发环境已启动"
    echo "API可通过 http://localhost:8000 访问"
    echo "PgAdmin可通过 http://localhost:5050 访问"
    echo "- 用户名: admin@example.com"
    echo "- 密码: admin"
fi

echo "容器状态:"
docker-compose ps 