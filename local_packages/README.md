# local_packages 目录

本目录用于存放在网络受限环境中使用的离线依赖包。

## 用途

1. 通过 `download_packages_for_offline.py` 脚本下载的依赖包会存放在此目录中
2. 使用 `install_dependencies.py` 配合 `--offline` 参数可以从此目录安装依赖包
3. 此目录下的包可以手动复制到无网络环境中使用

## 使用方法

### 下载离线包

```bash
# 下载所有requirements.txt中的依赖到本目录
python download_packages_for_offline.py

# 下载指定包
python download_packages_for_offline.py --packages "fastapi,sqlalchemy,celery"
```

### 离线安装

```bash
# 使用离线包安装
python install_dependencies.py --offline

# 指定源文件夹
python install_dependencies.py --offline --source ./local_packages
```

## 注意事项

- 请确保下载的包版本与requirements.txt中的版本一致
- 不同操作系统和Python版本可能需要不同的包版本
- 本目录不应包含在版本控制中（已在.gitignore中排除） 