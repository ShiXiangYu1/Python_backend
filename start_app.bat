@echo off
echo =======================================================
echo          Python后端项目启动脚本
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

:: 检查依赖是否已安装
pip show fastapi >nul 2>&1
if %errorlevel% NEQ 0 (
    echo 警告: 未检测到FastAPI，可能需要先安装依赖
    echo 是否立即运行依赖安装脚本？(y/n)
    set /p install_choice=
    if /i "%install_choice%"=="y" (
        call install_dependencies.bat
    ) else (
        echo 请先安装依赖后再运行此脚本
        pause
        exit /b 1
    )
)

echo.
echo 选择启动模式:
echo 1. 仅启动FastAPI应用
echo 2. 仅启动Celery Worker
echo 3. 仅启动Celery Beat (定时任务)
echo 4. 启动FastAPI应用和Celery Worker (推荐)
echo 5. 启动完整系统 (FastAPI + Celery Worker + Celery Beat)
echo.

set /p mode_choice=请输入选项 (1-5): 

:: 设置环境变量
echo 设置环境变量...
set PYTHONPATH=%CD%
set FASTAPI_ENV=development

:: 检查是否有虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 检测到虚拟环境，是否使用？(y/n)
    set /p venv_choice=
    if /i "%venv_choice%"=="y" (
        call venv\Scripts\activate.bat
        echo 已激活虚拟环境
    )
)

:: 启动应用
if "%mode_choice%"=="1" (
    echo 启动FastAPI应用...
    start "FastAPI应用" cmd /c "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & pause"
) else if "%mode_choice%"=="2" (
    echo 启动Celery Worker...
    start "Celery Worker" cmd /c "celery -A app.celery_app worker -l info & pause"
) else if "%mode_choice%"=="3" (
    echo 启动Celery Beat...
    start "Celery Beat" cmd /c "celery -A app.celery_app beat -l info & pause"
) else if "%mode_choice%"=="4" (
    echo 启动FastAPI应用和Celery Worker...
    start "FastAPI应用" cmd /c "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & pause"
    timeout /t 3 >nul
    start "Celery Worker" cmd /c "celery -A app.celery_app worker -l info & pause"
) else if "%mode_choice%"=="5" (
    echo 启动完整系统...
    start "FastAPI应用" cmd /c "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & pause"
    timeout /t 3 >nul
    start "Celery Worker" cmd /c "celery -A app.celery_app worker -l info & pause"
    timeout /t 3 >nul
    start "Celery Beat" cmd /c "celery -A app.celery_app beat -l info & pause"
    
    :: 启动Flower监控（如果已安装）
    pip show flower >nul 2>&1
    if %errorlevel% EQU 0 (
        echo 启动Flower监控...
        start "Celery Flower" cmd /c "celery -A app.celery_app flower --port=5555 & pause"
    )
) else (
    echo 无效的选项，请重新运行脚本。
    exit /b 1
)

echo.
echo 应用启动成功，请检查相应的命令窗口了解更多信息。
echo.

if "%mode_choice%"=="1" (
    echo FastAPI应用访问地址: http://localhost:8000
    echo API文档访问地址: http://localhost:8000/docs
) else if "%mode_choice%"=="4" (
    echo FastAPI应用访问地址: http://localhost:8000
    echo API文档访问地址: http://localhost:8000/docs
) else if "%mode_choice%"=="5" (
    echo FastAPI应用访问地址: http://localhost:8000
    echo API文档访问地址: http://localhost:8000/docs
    echo Flower监控访问地址: http://localhost:5555
)

echo.
echo 按任意键退出此启动脚本 (不会关闭已启动的应用)
pause 