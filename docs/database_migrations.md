# 数据库迁移指南

本文档提供有关数据库迁移的详细指南，包括设置、创建迁移、应用迁移和故障排除等内容。

## 概述

本项目使用Alembic作为数据库迁移工具，它是SQLAlchemy的官方迁移工具。Alembic提供了以下功能：

- 自动检测模型变化并生成迁移脚本
- 支持版本控制和回滚
- 管理数据库架构的演变历史

## 目录结构

```
alembic/
├── versions/              # 迁移脚本文件目录
├── env.py                 # Alembic环境配置
├── README                 # 使用指南
└── script.py.mako         # 迁移脚本模板
alembic.ini                # Alembic主配置文件
```

## 基本操作

### 初始设置

如果您是第一次设置项目，需要按照以下步骤操作：

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行初始迁移：
```bash
alembic upgrade head
```

3. 填充初始数据：
```bash
python scripts/seed_db.py
```

### 创建新的迁移

当您对数据库模型进行更改后，需要创建新的迁移脚本：

```bash
alembic revision --autogenerate -m "描述您的更改"
```

生成的迁移脚本将放置在`alembic/versions/`目录中。建议您在提交前检查生成的迁移脚本，确保自动生成的迁移符合预期。

### 应用迁移

应用所有未应用的迁移：

```bash
alembic upgrade head
```

应用到特定版本：

```bash
alembic upgrade <revision_id>
```

### 回滚迁移

回滚到上一个版本：

```bash
alembic downgrade -1
```

完全回滚所有迁移：

```bash
alembic downgrade base
```

## 环境特定配置

### 开发环境

在开发环境中，我们默认使用SQLite数据库：

```
DATABASE_URL=sqlite:///app.db
```

### 生产环境

在生产环境中，我们使用PostgreSQL数据库：

```
DATABASE_URL=postgresql+asyncpg://username:password@host:port/database
```

## 最佳实践

1. **定期创建迁移**：在每次对模型进行更改后及时创建迁移，而不是一次性累积多个更改

2. **提交迁移到版本控制**：所有迁移脚本都应该提交到版本控制系统中

3. **测试迁移**：在应用到生产环境前，先在测试环境中测试迁移

4. **备份数据**：在运行迁移之前备份数据库

5. **审核自动生成的迁移**：检查Alembic自动生成的迁移脚本是否符合预期

## 常见问题

### 问题：自动检测无法正确识别某些更改

**解决方案**：手动编辑迁移脚本或创建手动迁移脚本：

```bash
alembic revision -m "手动迁移描述"
```

然后编辑生成的脚本，手动添加必要的更改。

### 问题：迁移失败

**解决方案**：

1. 检查错误消息，确定失败原因
2. 如果可能，修复问题并重新运行迁移
3. 如果需要，回滚到上一个已知良好的版本：`alembic downgrade <revision_id>`

### 问题：冲突的迁移

**解决方案**：

1. 确保在创建新迁移之前更新到最新版本
2. 如果有多个开发人员同时创建迁移，可能需要手动解决冲突

## 进阶技巧

### 分支迁移

Alembic支持分支迁移，这在处理并行开发时很有用：

```bash
alembic revision --head=<parent_revision> -m "分支迁移"
```

### 数据迁移

除了架构更改外，有时还需要迁移数据：

```python
def upgrade():
    # 架构更改
    op.add_column('users', sa.Column('new_column', sa.String()))
    
    # 数据迁移
    connection = op.get_bind()
    connection.execute("UPDATE users SET new_column = 'default_value'")
``` 