# 项目文档目录

本目录包含项目的各种技术文档和用户指南。

## 文档列表

### 任务系统文档

- [任务系统架构](task_system_architecture.md) - 详细介绍任务系统的架构设计和实现原理
- [任务系统使用指南](task_system_guide.md) - 关于如何使用和管理任务系统的详细说明

### 服务器和部署文档

- [简化服务器说明](simplified_server.md) - 简化版HTTP服务器的使用说明和配置选项
- [数据库迁移指南](database_migrations.md) - 数据库版本控制和迁移的详细说明

### 测试文档

- [测试工具说明](testing_tools.md) - 项目中使用的各种测试工具的详细使用说明

## 文档格式和标准

所有文档均使用Markdown格式编写，遵循以下规范：

1. 使用清晰的标题结构（# 一级标题，## 二级标题，等）
2. 代码块使用```符号包围，并指定语言类型
3. 使用表格展示结构化数据
4. 使用链接引用其他文档或外部资源
5. 使用图片说明复杂概念（图片存储在`assets`目录）

## 文档维护

在对项目进行重大更改时，请同步更新相关文档。文档更新应包括：

1. 新功能的使用说明
2. 配置选项的变更说明
3. API接口的变更
4. 架构调整的原因和影响

## 文档构建

项目支持使用MkDocs将这些Markdown文档构建为静态网站：

```bash
# 安装MkDocs
pip install mkdocs

# 本地预览
mkdocs serve

# 构建静态站点
mkdocs build
```

构建后的文档将位于`site`目录，可以部署到任何静态网站托管服务。 