# Python后端任务处理系统

这是一个基于FastAPI和Celery的异步任务处理系统，用于处理后台长时间运行的任务。

## 功能特点

- 基于FastAPI构建的高性能REST API
- 使用Celery处理异步任务
- 支持任务创建、查询、取消和删除
- 任务进度实时更新和状态同步
- 支持多种任务优先级
- 提供完善的任务管理API

## 系统架构

系统由以下主要组件构成：

1. **API层**：基于FastAPI的RESTful API，处理HTTP请求
2. **服务层**：业务逻辑处理，包括用户管理、任务管理等
3. **任务系统**：基于Celery的异步任务处理框架
4. **数据层**：采用SQLAlchemy ORM和关系型数据库存储数据

## 目录结构

```
app/
├── api/               # API相关代码
│   ├── deps.py        # 依赖项（认证等）
│   ├── routes.py      # API路由配置
│   └── endpoints/     # API端点
│       ├── auth.py    # 认证API
│       ├── users.py   # 用户API
│       └── tasks.py   # 任务API
├── core/              # 核心配置
│   ├── config.py      # 系统配置
│   └── security.py    # 安全相关
├── db/                # 数据库相关
│   └── session.py     # 数据库会话
├── models/            # 数据模型
│   ├── user.py        # 用户模型
│   └── task.py        # 任务模型
├── schemas/           # Pydantic模型/校验
│   ├── user.py        # 用户模式
│   └── task.py        # 任务模式
├── services/          # 服务层
│   ├── user_service.py # 用户服务
│   └── task_service.py # 任务服务
├── tasks/             # Celery任务
│   ├── __init__.py    # 任务初始化
│   ├── common_tasks.py # 通用任务
│   ├── model_tasks.py  # 模型相关任务
│   └── high_priority_tasks.py # 高优先级任务
├── celery_app.py      # Celery应用配置
└── main.py            # 主应用入口
```

## 快速开始

### 环境要求

- Python 3.8+
- Redis (用于Celery消息代理)
- PostgreSQL (或其他关系型数据库)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

创建`.env`文件并设置以下环境变量：

```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=your-secret-key
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 启动API服务

```bash
uvicorn app.main:app --reload
```

### 启动Celery Worker

```bash
celery -A app.celery_app worker -l info
```

### 启动Celery Beat (定时任务)

```bash
celery -A app.celery_app beat -l info
```

## 任务系统使用

### 创建任务

```python
from app.services.task_service import task_service

# 创建任务
task, celery_id = task_service.create_task(
    db=db,
    name="测试任务",
    task_type="test_task",
    celery_task_name="app.tasks.common_tasks.long_running_task",
    args=[30],  # 任务参数
    kwargs={},  # 任务关键字参数
    priority="normal",
    user_id=current_user.id
)

# 获取任务ID
task_id = task.id
```

### 查询任务状态

```python
# 获取任务信息
task = task_service.get_task(db, task_id)

# 获取任务状态
status = task.status  # pending, running, succeeded, failed, revoked

# 获取任务进度
progress = task.progress  # 0-100

# 获取任务结果
result = task.result  # JSON格式的结果
```

### 取消任务

```python
# 取消正在运行的任务
success = task_service.cancel_task(db, task_id)
```

### 删除任务

```python
# 删除任务记录
success = task_service.delete_task(db, task_id)
```

## 任务API使用示例

### 创建任务

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
    "priority": "normal"
  }'
```

### 获取任务列表

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/" \
  -H "Authorization: Bearer $TOKEN"
```

### 获取任务详情

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/{task_id}" \
  -H "Authorization: Bearer $TOKEN"
```

### 取消任务

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/{task_id}/cancel" \
  -H "Authorization: Bearer $TOKEN"
```

## Celery配置

### 队列配置

系统配置了多个队列来处理不同优先级的任务：

- `high_priority`: 处理紧急和高优先级任务
- `default`: 处理普通优先级任务
- `low_priority`: 处理低优先级任务

### 定义Celery任务

```python
from app.celery_app import celery_app

@celery_app.task(bind=True, name="app.tasks.example_task")
def example_task(self, arg1, arg2, task_id=None):
    """
    示例任务
    """
    # 任务逻辑实现
    result = {}
    
    # 返回结果
    return result
```

### 自定义任务基类

系统定义了自定义任务基类`SQLAlchemyTask`，用于处理数据库会话和任务状态更新：

```python
class SQLAlchemyTask(Task):
    """
    集成SQLAlchemy会话管理的Celery任务基类
    """
    abstract = True
    
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """任务完成后关闭数据库会话"""
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            db.close()
        except:
            pass
        super().after_return(status, retval, task_id, args, kwargs, einfo)
```

## 测试

系统包含完整的单元测试，覆盖API和Celery任务：

```bash
# 运行测试
pytest
```

## 开发指南

### 添加新的API端点

1. 在`app/api/endpoints/`目录中创建新的模块
2. 在`app/api/routes.py`中注册路由

### 添加新的任务

1. 在`app/tasks/`目录下的合适模块中定义新任务
2. 确保任务被导入到`app/tasks/__init__.py`

### 任务状态更新

任务应该定期更新其进度和状态：

```python
from app.services.task_service import TaskService

task_service = TaskService()

# 更新任务进度
task_service.update_task_progress(db, task_id, 50, {"status": "processing", "step": 2})

# 更新任务状态
task_service.update_task_status(db, task_id, "succeeded", 100, {"result": "success"})
```

## 许可证

MIT 