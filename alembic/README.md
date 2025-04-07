# Alembic数据库迁移指南

此目录包含使用Alembic管理数据库迁移的脚本和配置。

## 目录结构

- `versions/` - 存放迁移脚本文件
- `env.py` - Alembic环境配置
- `script.py.mako` - 迁移脚本模板

## 基本命令

### 创建新的迁移脚本

```bash
# 自动检测模型变化（当env.py正确配置时）
alembic revision --autogenerate -m "描述变更内容"

# 手动创建迁移脚本（不检测模型变化）
alembic revision -m "描述变更内容"
```

### 运行迁移

```bash
# 更新到最新版本
alembic upgrade head

# 更新到指定版本
alembic upgrade <revision_id>

# 更新指定数量的版本
alembic upgrade +2  # 向前更新2个版本

# 回滚到前一个版本
alembic downgrade -1

# 完全回滚所有迁移
alembic downgrade base
```

### 查看迁移状态

```bash
# 显示当前迁移版本
alembic current

# 显示迁移历史
alembic history --verbose
```

## 迁移文件

迁移文件位于`versions`目录下，每个文件包含两个主要函数：

- `upgrade()`: 应用迁移的变更
- `downgrade()`: 回滚迁移的变更

## 使用示例

创建新表和修改现有表：

```python
def upgrade():
    # 创建新表
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('key_hash', sa.String(128), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('expired_at', sa.DateTime, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
    )
    
    # 修改现有表
    op.add_column('users', sa.Column('last_login', sa.DateTime, nullable=True))
```

## 注意事项

1. 建议在生产环境应用迁移前，先在测试环境进行测试
2. 对已经应用的迁移文件不要做修改，而是创建新的迁移文件
3. 如果自动检测不正确，可以手动编写迁移脚本
4. 确保数据库备份在执行迁移前已完成
5. 在CI/CD流程中，建议包含自动数据库迁移步骤

## 其他资源

详细的数据库迁移策略和最佳实践，请参考 [docs/database_migrations.md](../docs/database_migrations.md) 文档。 