@echo off
echo =======================================================
echo         Python后端项目简易服务器启动脚本
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

echo 启动简易HTTP服务器...
echo.
echo 简易服务器提供基本API功能，不依赖于完整的FastAPI和Celery环境。
echo 适用于开发和测试阶段，或在无法启动完整应用时使用。
echo.
echo 按Ctrl+C停止服务器。
echo.

:: 设置环境变量
set PYTHONPATH=%CD%

:: 启动简易HTTP服务器
python app/simplified_main.py

pause 