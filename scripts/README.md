# 脚本目录 (scripts)

本目录包含各种用于项目开发、测试、部署和维护的脚本文件。

## 开发脚本

- `run_simple_server.py` - 启动一个简化版的HTTP服务器，用于开发调试
- `local_server.py` - 启动本地开发服务器，包含更多配置选项
- `check_server.py` - 检查服务器状态和可用性的脚本

## 测试脚本

- `integration_test.py` - 完整的集成测试框架
- `simple_integration_test.py` - 简化版的集成测试工具
- `run_integration_tests.py` - 运行所有集成测试的脚本
- `performance_test.py` - 性能测试工具
- `security_scan.py` - 安全扫描工具
- `verify_components.py` - 验证项目组件和依赖的脚本

## Celery任务队列脚本

- `celery_worker.py` - 启动Celery Worker进程
- `celery_beat.py` - 启动Celery Beat定时任务调度器

## 数据库脚本

- `seed_db.py` - 数据库种子数据初始化脚本
- `seed_db_simple.py` - 简化版数据库初始化脚本

## Docker部署脚本

- `docker-build.sh` - 构建Docker镜像的脚本
- `docker-deploy.sh` - 部署Docker容器的脚本
- `docker-entrypoint.sh` - Docker容器的入口点脚本

## 使用说明

大多数Python脚本可以直接通过Python解释器运行：

```bash
python scripts/脚本名称.py [参数]
```

Shell脚本需要执行权限：

```bash
chmod +x scripts/脚本名称.sh
./scripts/脚本名称.sh [参数]
```

详细的参数和选项可以通过运行脚本的帮助选项查看：

```bash
python scripts/脚本名称.py --help
``` 