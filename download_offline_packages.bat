@echo off
echo =======================================================
echo          下载Python后端项目离线依赖包
echo =======================================================
echo.

:: 检查Python是否已安装
python --version >nul 2>&1
if %errorlevel% NEQ 0 (
    echo 错误: 未检测到Python，请确保已安装Python并添加到PATH环境变量中
    echo 您可以从 https://www.python.org/downloads/ 下载并安装Python
    pause
    exit /b 1
)

echo 已检测到Python，开始准备下载离线依赖包...
echo.

echo 选择镜像源:
echo 1. 默认PyPI源 (官方源)
echo 2. 清华镜像 (国内推荐)
echo 3. 阿里云镜像
echo 4. 豆瓣镜像
echo 5. 华为云镜像
echo.

set /p choice=请输入选项 (1-5): 

set INDEX_URL=
set MIRROR_NAME=默认PyPI源

if "%choice%"=="1" (
    set INDEX_URL=
    set MIRROR_NAME=默认PyPI源
) else if "%choice%"=="2" (
    set INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
    set MIRROR_NAME=清华镜像
) else if "%choice%"=="3" (
    set INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
    set MIRROR_NAME=阿里云镜像
) else if "%choice%"=="4" (
    set INDEX_URL=https://pypi.doubanio.com/simple/
    set MIRROR_NAME=豆瓣镜像
) else if "%choice%"=="5" (
    set INDEX_URL=https://repo.huaweicloud.com/repository/pypi/simple
    set MIRROR_NAME=华为云镜像
) else (
    echo 无效的选项，使用默认PyPI源...
)

echo.
echo 选择输出目录:
echo 1. 默认目录 (offline_packages)
echo 2. 自定义目录
echo.

set /p dir_choice=请输入选项 (1-2): 

set OUTPUT_DIR=offline_packages

if "%dir_choice%"=="2" (
    set /p OUTPUT_DIR=请输入自定义输出目录名称: 
)

echo.
echo 开始下载过程:
echo - 使用镜像源: %MIRROR_NAME%
echo - 输出目录: %OUTPUT_DIR%
echo.

if not exist "%~dp0download_packages_for_offline.py" (
    echo 错误: 找不到下载脚本 download_packages_for_offline.py
    echo 请确保该脚本与此批处理文件在同一目录
    pause
    exit /b 1
)

if "%INDEX_URL%"=="" (
    python "%~dp0download_packages_for_offline.py" --output-dir "%OUTPUT_DIR%"
) else (
    python "%~dp0download_packages_for_offline.py" --output-dir "%OUTPUT_DIR%" --index-url "%INDEX_URL%"
)

echo.
echo 下载过程已完成。
if exist "%OUTPUT_DIR%" (
    echo 离线安装包保存在目录: %~dp0%OUTPUT_DIR%
    echo 您可以将此目录传输到目标机器上，然后运行其中的install_offline.bat脚本。
)
pause 