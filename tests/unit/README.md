# 单元测试说明

## 概述

本目录包含项目的单元测试，主要测试各个组件的功能和行为，确保它们按预期工作。这些测试是独立的，不依赖于外部服务或系统状态。

## 测试结构

### 任务相关测试

- `test_task_status_update.py`: 测试SQLAlchemyTask的任务状态更新方法
- `test_batch_process.py`: 测试SQLAlchemyTask的批处理方法

## 运行测试

### 使用测试脚本

项目提供了一个简单的测试运行脚本，可以通过以下方式运行：

```bash
# 运行所有单元测试
python tests/run_unit_tests.py

# 运行特定测试文件
python tests/run_unit_tests.py tests/unit/test_task_status_update.py

# 运行详细输出
python tests/run_unit_tests.py -v

# 在第一个失败测试停止
python tests/run_unit_tests.py -x
```

### 使用pytest直接运行

也可以直接使用pytest运行测试：

```bash
# 运行所有单元测试
pytest tests/unit

# 运行特定测试文件
pytest tests/unit/test_task_status_update.py

# 运行详细输出
pytest -v tests/unit

# 在第一个失败测试停止
pytest -x tests/unit
```

## 编写新测试

编写新的单元测试时，请遵循以下原则：

1. 每个测试函数应专注于测试一个小功能点
2. 使用`assert`语句验证结果
3. 使用`unittest.mock`模块模拟依赖项
4. 避免在测试中使用外部服务（如数据库、Redis等）
5. 使用`pytest.fixture`共享测试设置
6. 为测试添加详细的文档字符串，说明测试目的

### 示例

```python
def test_example_function():
    """测试示例函数的行为"""
    # 设置测试数据
    input_data = {"key": "value"}
    
    # 调用被测函数
    result = example_function(input_data)
    
    # 验证结果
    assert result == expected_result
```

## 测试覆盖率

推荐使用`pytest-cov`插件检查测试覆盖率：

```bash
# 安装pytest-cov
pip install pytest-cov

# 运行测试并生成覆盖率报告
pytest --cov=app tests/unit

# 生成HTML覆盖率报告
pytest --cov=app --cov-report=html tests/unit
```