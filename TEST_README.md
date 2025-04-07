# 性能与安全测试工具

这个项目提供了一套全面的工具，用于测试API系统的性能和安全性。通过这些工具，您可以评估系统在不同负载下的表现，检测潜在的安全漏洞，并生成详细的报告以帮助优化系统。

## 测试脚本概述

本项目包含以下主要测试脚本：

1. **性能测试脚本 (performance_test.py)**：
   - 测试API端点的响应时间
   - 测试并发负载处理能力
   - 测试系统资源利用情况
   - 生成详细的性能报告

2. **安全测试脚本 (security_test.py)**：
   - 测试身份验证和授权机制
   - 测试输入验证和SQL注入防护
   - 测试XSS和CSRF防护
   - 测试安全HTTP头配置
   - 生成安全评估报告

3. **集成运行脚本 (run_tests.py)**：
   - 集成运行性能和安全测试
   - 生成综合测试报告
   - 提供命令行参数控制测试行为

## 安装依赖

在运行测试之前，请确保已安装所有必要的依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

### 运行所有测试

```bash
python run_tests.py --all
```

### 仅运行性能测试

```bash
python run_tests.py --performance
```

### 仅运行安全测试

```bash
python run_tests.py --security
```

### 运行测试并显示详细输出

```bash
python run_tests.py --all --verbose
```

## 测试报告

测试完成后，将在`test_reports`目录下生成以下报告：

- **综合测试报告**：`test_reports/combined_report.md`
- **性能测试报告**：`test_reports/performance/performance_report_*.md`
- **性能测试图表**：`test_reports/performance/performance_chart_*.png`
- **安全测试报告**：`test_reports/security/security_report_*.txt`
- **安全测试结果**：`test_reports/security/security_results_*.json`

## 自定义测试

### 性能测试自定义

如需自定义性能测试，可以编辑`performance_test.py`中的以下配置：

```python
BASE_URL = "http://localhost:8000"  # 测试服务器地址
API_PREFIX = "/api/v1"              # API前缀
MAX_CONCURRENT_REQUESTS = 50        # 最大并发请求数
REQUEST_COUNT = 200                 # 每个端点的请求总数
TEST_ENDPOINTS = [                  # 要测试的端点列表
    {"name": "获取当前用户", "method": "GET", "path": "/users/me", "auth_required": True},
    {"name": "获取AI模型列表", "method": "GET", "path": "/models", "auth_required": True},
    {"name": "健康检查", "method": "GET", "path": "/health", "auth_required": False},
]
```

### 安全测试自定义

如需自定义安全测试，可以编辑`security_test.py`中的以下配置：

```python
BASE_URL = "http://localhost:8000"  # 测试服务器地址
API_PREFIX = "/api/v1"              # API前缀
TEST_USER = {"username": "sxy", "password": "sxy123456"}  # 测试用户凭据
```

## 最佳实践

1. **在开发环境中测试**：首先在隔离的开发环境中运行测试，避免对生产系统造成干扰。

2. **定期运行测试**：定期运行测试可以及早发现性能下降或安全问题。

3. **修复后重新测试**：在修复问题后，重新运行测试以验证修复是否有效。

4. **监控资源使用**：关注测试报告中的资源使用情况，及时发现潜在的性能瓶颈。

5. **关注安全警告**：即使是小的安全警告也可能表明存在更严重的问题，应该认真对待。

## 故障排除

### 测试脚本无法运行

- 确保已安装所有依赖：`pip install -r requirements.txt`
- 检查Python版本是否为3.7+：`python --version`
- 确保测试服务器正在运行并可访问

### 测试结果不准确

- 确保测试环境不受其他进程的干扰
- 增加请求次数以获得更可靠的结果
- 在多个时间点运行测试以获取平均值

### 依赖冲突

- 考虑使用虚拟环境：`python -m venv venv`
- 使用特定版本的依赖：见`requirements.txt`

## 安全注意事项

- 这些测试脚本可能会产生大量请求，可能触发DoS防护机制
- 安全测试包含可能被误认为是攻击的行为，请仅在您有权测试的系统上使用
- 不要在生产环境直接进行负载测试，除非您已经采取了适当的预防措施

## 贡献

欢迎对这些测试工具进行改进和扩展。如有任何问题或建议，请联系系统管理员。 