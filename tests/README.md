# 测试目录

本目录包含项目的所有测试代码，包括单元测试、集成测试和前端测试。

## 目录结构

- `api/` - API端点的测试
- `fixtures/` - 测试数据和固定装置
- `frontend/` - 前端代码的测试
- `integration/` - 系统集成测试
- `services/` - 服务层的测试
- `unit/` - 其他单元测试

## 测试文件

- `conftest.py` - Pytest固定装置和共享测试资源
- `run_unit_tests.py` - 单元测试运行脚本
- `test_celery_tasks.py` - Celery任务测试
- `test_celery_scripts.py` - Celery脚本测试
- `test_tasks_api.py` - 任务API测试
- `test_task_service.py` - 任务服务层测试

## 运行测试

### 运行所有测试

```bash
# 使用pytest直接运行
pytest

# 使用项目提供的批处理脚本
run_unit_tests.bat
```

### 运行特定测试模块

```bash
# 运行特定测试文件
pytest tests/test_celery_tasks.py

# 运行特定测试目录下的所有测试
pytest tests/unit/
```

### 运行特定测试函数

```bash
# 运行特定测试函数
pytest tests/test_celery_tasks.py::test_create_task

# 运行特定测试类中的特定方法
pytest tests/unit/test_models.py::TestUserModel::test_create_user
```

## 测试标记

使用pytest标记筛选运行特定类型的测试：

```bash
# 运行所有快速测试
pytest -m "fast"

# 运行数据库相关测试
pytest -m "db"

# 运行API测试但排除慢速测试
pytest -m "api and not slow"
```

可用的标记包括：

- `unit`: 单元测试
- `integration`: 集成测试
- `api`: API测试
- `db`: 数据库测试
- `auth`: 认证相关测试
- `slow`: 运行时间较长的测试
- `models`: 模型测试
- `tasks`: 任务系统测试

## 测试覆盖率

使用pytest-cov收集测试覆盖率数据：

```bash
# 生成覆盖率报告
pytest --cov=app

# 生成HTML覆盖率报告
pytest --cov=app --cov-report=html

# 生成XML覆盖率报告（用于CI/CD服务）
pytest --cov=app --cov-report=xml
```

覆盖率报告将保存在`test_reports/coverage/`目录下。

## 前端测试

前端测试使用Jest框架：

```bash
# 运行所有前端测试
cd frontend && npm test

# 运行特定前端测试文件
cd frontend && npm test -- src/components/Login.test.js
```

## 编写新测试

添加新测试时，请遵循以下规范：

1. 测试文件应放在对应的目录中（`api/`, `unit/`, `integration/`等）
2. 测试文件名应以`test_`开头
3. 测试函数名也应以`test_`开头
4. 使用适当的标记标识测试类型
5. 每个测试应该专注于测试一个功能点
6. 使用固定装置和mock来隔离测试环境

详细的测试编写指南可参考 [docs/testing_tools.md](../docs/testing_tools.md)。 