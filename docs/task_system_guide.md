# 任务系统使用指南

## 1. 概述

任务系统是一个基于FastAPI和Celery的异步任务处理框架，用于处理长时间运行的后台任务。该系统提供了任务创建、查询、取消和删除等功能，以及任务状态的实时更新和进度跟踪。

### 1.1 主要功能

- 异步任务处理
- 任务优先级和队列管理
- 任务状态和进度跟踪
- 任务结果存储和检索
- 定时任务调度
- 任务执行监控和统计

### 1.2 架构组件

- **API层**：基于FastAPI的RESTful API
- **服务层**：任务业务逻辑
- **数据层**：任务数据存储
- **Celery Worker**：任务执行引擎
- **Celery Beat**：定时任务调度器
- **Redis**：消息代理和结果后端
- **Flower**：任务监控界面

## 2. 快速开始

### 2.1 安装和配置

1. 确保已安装必要的依赖：

```bash
pip install -r requirements.txt
```

2. 配置环境变量（创建`.env`文件）：

```
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

3. 启动Redis（如果尚未启动）：

```bash
docker run -d -p 6379:6379 redis:alpine
```

### 2.2 启动服务

**使用Docker Compose启动**：

```bash
docker-compose -f docker-compose.celery.yml up -d
```

**手动启动**：

1. 启动API服务：

```bash
uvicorn app.main:app --reload
```

2. 启动Celery Worker：

```bash
python -m scripts.celery_worker
```

3. 启动Celery Beat（用于定时任务）：

```bash
python -m scripts.celery_beat
```

4. 启动Flower监控（可选）：

```bash
celery flower -A app.celery_app.celery_app
```

### 2.3 API接口访问

API文档可通过以下地址访问：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 3. 任务管理

### 3.1 创建任务

**通过API创建**：

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "数据处理任务",
    "task_type": "data_processing",
    "celery_task_name": "app.tasks.common_tasks.long_running_task",
    "args": [60],
    "kwargs": {"param": "value"},
    "priority": 2
  }'
```

**通过服务层创建**：

```python
from app.services.task import task_service

task, celery_id = await task_service.create_task(
    db=db,
    name="数据处理任务",
    task_type="data_processing",
    celery_task_name="app.tasks.common_tasks.long_running_task",
    args=[60],
    kwargs={"param": "value"},
    priority=2,
    user_id=user_id
)
```

### 3.2 查询任务

**获取任务详情**：

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/{task_id}" \
  -H "Authorization: Bearer $TOKEN"
```

**获取任务列表**：

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/?status=running&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

**通过服务层查询**：

```python
# 获取单个任务
task = await task_service.get_task(db, task_id)

# 获取任务列表
tasks = await task_service.get_tasks(
    db=db,
    status="running",
    task_type="data_processing",
    skip=0,
    limit=10
)
```

### 3.3 取消任务

**通过API取消**：

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/{task_id}/cancel" \
  -H "Authorization: Bearer $TOKEN"
```

**通过服务层取消**：

```python
success = await task_service.cancel_task(db, task_id)
```

### 3.4 删除任务

**通过API删除**：

```bash
curl -X DELETE "http://localhost:8000/api/v1/tasks/{task_id}" \
  -H "Authorization: Bearer $TOKEN"
```

**通过服务层删除**：

```python
success = await task_service.delete_task(db, task_id)
```

## 4. 自定义任务实现

### 4.1 创建新任务

在`app/tasks/`目录下创建新的任务函数：

```python
from app.celery_app import celery_app
from app.models.task import TaskStatus

@celery_app.task(bind=True)
def my_custom_task(self, param1, param2, task_id=None):
    """
    自定义任务实现
    """
    # 初始化任务状态
    if task_id:
        import asyncio
        from app.services.task import TaskService
        from app.db.session import async_session
        
        async def update_status():
            async with async_session() as session:
                task_service = TaskService()
                await task_service.update_task_status(
                    db=session,
                    task_id=task_id,
                    status=TaskStatus.RUNNING,
                    progress=0
                )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(update_status())
        loop.close()
    
    # 任务实现...
    result = {}
    
    # 更新任务进度
    if task_id:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            update_status()
        )
        loop.close()
    
    return result
```

### 4.2 注册任务

确保任务被导入，在`app/tasks/__init__.py`中导入新任务：

```python
from app.tasks.my_module import my_custom_task
```

### 4.3 配置任务路由

在`app/celery_app.py`的任务路由中添加新任务的路由规则：

```python
"app.tasks.my_module.my_custom_task": {
    "queue": "default",
    "routing_key": "default.tasks"
},
```

## 5. 监控和维护

### 5.1 使用Flower监控

访问Flower监控界面：`http://localhost:5555`

主要功能：
- 查看活跃的任务和Worker
- 查看任务执行历史
- 取消正在执行的任务
- 查看任务详情和结果
- 监控队列长度和系统资源使用

### 5.2 任务日志

任务执行日志保存在以下位置：
- Worker日志：`logs/celery_worker.log`
- Beat日志：`logs/celery_beat.log`
- 应用日志：`logs/app.log`

### 5.3 常见问题排查

**任务未执行**：
- 检查Redis服务是否正常运行
- 确认Celery Worker是否启动
- 检查任务路由配置是否正确

**任务执行失败**：
- 检查日志文件中的错误信息
- 确认任务参数是否正确
- 检查任务函数实现是否存在问题

**任务卡在"待处理"状态**：
- 确认Worker正在监听正确的队列
- 检查Redis连接是否正常
- 重启Celery Worker

## 6. 最佳实践

### 6.1 任务设计原则

- **幂等性**：任务应该设计为可以安全地重复执行
- **状态管理**：定期更新任务状态和进度
- **错误处理**：捕获并记录异常，实现适当的重试机制
- **资源释放**：确保任务完成后释放所有资源
- **超时控制**：设置合理的任务超时时间

### 6.2 任务优先级管理

系统支持四个优先级级别：
- `1`：低优先级（LOW）
- `2`：普通优先级（NORMAL）
- `3`：高优先级（HIGH）
- `4`：关键优先级（CRITICAL）

根据任务的重要性和紧急程度选择合适的优先级。

### 6.3 长时间运行任务的处理

对于长时间运行的任务：
- 定期更新任务进度
- 实现取消机制
- 考虑将大任务拆分为多个小任务
- 使用检查点机制保存中间状态

### 6.4 定时任务配置

在`app/celery_app.py`中配置定时任务：

```python
beat_schedule={
    "task-name": {
        "task": "app.tasks.module.task_function",
        "schedule": 3600.0,  # 每小时执行一次
        "args": (arg1, arg2),
        "kwargs": {"param": "value"},
        "options": {"queue": "default"},
    },
}
```

## 7. API参考

### 7.1 任务API端点

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/tasks/ | 创建新任务 |
| GET | /api/v1/tasks/ | 获取任务列表 |
| GET | /api/v1/tasks/{task_id} | 获取任务详情 |
| PATCH | /api/v1/tasks/{task_id} | 更新任务状态 |
| DELETE | /api/v1/tasks/{task_id} | 删除任务 |
| POST | /api/v1/tasks/{task_id}/cancel | 取消任务 |
| GET | /api/v1/tasks/count | 获取任务统计 |

### 7.2 任务状态

| 状态 | 描述 |
|------|------|
| pending | 任务已创建但尚未执行 |
| running | 任务正在执行中 |
| succeeded | 任务已成功完成 |
| failed | 任务执行失败 |
| revoked | 任务已被取消 |

## 8. 故障排除

### 8.1 常见错误

**错误：无法连接到Redis**

```
kombu.exceptions.OperationalError: Error 111 connecting to localhost:6379. Connection refused.
```

解决方案：
- 确认Redis服务已启动
- 检查Redis连接URL是否正确
- 检查防火墙设置

**错误：任务执行超时**

```
celery.exceptions.TimeoutError: Task app.tasks.module.task_function timed out after 300.0s
```

解决方案：
- 增加任务超时时间
- 优化任务执行效率
- 拆分为多个小任务

**错误：任务路由问题**

```
Task app.tasks.module.task_function not registered
```

解决方案：
- 确认任务模块已正确导入
- 检查celery_app.py中的include配置
- 确认Worker正在监听正确的队列

### 8.2 任务执行失败的调试方法

1. 检查日志文件，查找错误信息
2. 使用Flower查看任务详情和traceback
3. 尝试在同步模式下执行任务函数
4. 增加日志输出，追踪任务执行过程

## 9. 附录

### 9.1 环境变量参考

| 变量 | 描述 | 默认值 |
|------|------|--------|
| CELERY_BROKER_URL | Celery消息代理URL | redis://localhost:6379/0 |
| CELERY_RESULT_BACKEND | Celery结果后端URL | redis://localhost:6379/0 |
| CELERY_TASK_SERIALIZER | 任务序列化格式 | json |
| CELERY_RESULT_SERIALIZER | 结果序列化格式 | json |
| CELERY_TIMEZONE | 时区设置 | Asia/Shanghai |
| CELERY_WORKER_CONCURRENCY | Worker并发数 | CPU核心数 |
| FLOWER_USER | Flower认证用户名 | admin |
| FLOWER_PASSWORD | Flower认证密码 | admin |

### 9.2 相关资源链接

- [Celery官方文档](https://docs.celeryproject.org/)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [Redis官方文档](https://redis.io/documentation)
- [SQLAlchemy官方文档](https://docs.sqlalchemy.org/)

### 9.3 任务系统更新日志

**v1.0.0 (2025-04-03)**
- 初始版本发布
- 基本的任务创建、查询、取消和删除功能
- 任务状态和进度追踪
- Docker容器化支持

**计划功能**
- 任务执行统计和报告
- 批量任务操作
- 任务依赖关系支持
- 更强大的错误处理和重试机制 