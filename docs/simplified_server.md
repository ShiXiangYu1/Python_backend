# 简化版API服务器使用说明

## 简介

本文档介绍了如何使用简化版API服务器，该服务器是为解决依赖安装问题而设计的替代方案。简化版服务器**不依赖**FastAPI、Uvicorn等第三方库，仅使用Python标准库实现，可在无法安装完整依赖的环境中运行。

## 功能特点

1. **零依赖**: 仅使用Python标准库，无需额外安装任何第三方包
2. **兼容API**: 提供与完整版API相同的接口路径和响应格式
3. **基本数据服务**: 支持模型列表、用户信息、API密钥等基本数据访问
4. **简易UI**: 提供简单的Web界面，方便访问和测试API

## 启动方法

### 方法一：使用脚本启动

最简单的方式是使用提供的启动脚本：

```bash
python scripts/run_simple_server.py
```

### 方法二：直接运行模块

也可以直接运行主模块：

```bash
python app/simplified_main.py
```

## 可用API端点

启动服务器后，可以通过以下URL访问API：

| 端点 | 请求方法 | 说明 |
|------|---------|------|
| `/api/v1/health` | GET | 系统健康状态检查 |
| `/api/v1/models` | GET | 获取模型列表 |
| `/api/v1/users/me` | GET | 获取当前用户信息 |
| `/api/v1/api-keys` | GET | 获取API密钥列表 |
| `/api/v1/system-info` | GET | 获取系统信息 |
| `/api/v1/database-info` | GET | 获取数据库信息 |

## Web界面

服务器启动后，可以通过浏览器访问 `http://localhost:8000` 打开Web界面。界面提供了各API端点的链接和基本说明。

## 限制和注意事项

1. 简化版服务器仅支持GET请求，不支持POST、PUT、DELETE等其他HTTP方法
2. 数据来源为本地SQLite数据库，如果数据库文件不存在，某些API会返回错误
3. 简化版服务器仅适用于开发和测试目的，不适合生产环境使用
4. 没有用户认证和权限控制功能，所有API都可以直接访问

## 与完整版的区别

| 功能 | 简化版 | 完整版 |
|------|--------|--------|
| 依赖 | 仅使用标准库 | 需要FastAPI、SQLAlchemy等多个依赖 |
| API文档 | 简易HTML页面 | 支持Swagger/ReDoc自动文档 |
| 请求方法 | 仅支持GET | 支持完整HTTP方法 |
| 数据操作 | 仅读取操作 | 支持完整的CRUD操作 |
| 性能 | 低 | 高 |

## 切换到完整版

当环境问题解决后，建议切换回完整版API服务器以获得更完整的功能。切换方法：

1. 安装所有依赖：`pip install -r requirements.txt`
2. 启动完整版服务器：`python -m uvicorn app.main:app --reload`

## 故障排除

如果启动服务器时遇到问题，请检查：

1. Python版本是否为3.6或更高版本
2. 数据库文件app.db是否存在
3. 端口8000是否被其他程序占用

如果端口被占用，可以修改`app/simplified_main.py`文件中的`PORT`常量，将其改为其他可用端口。 