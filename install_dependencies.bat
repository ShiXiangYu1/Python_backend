@echo off
echo =======================================================
echo          Python后端项目依赖安装脚本
echo =======================================================
echo.

:: 检查是否以管理员身份运行
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo 提示: 建议以管理员身份运行此脚本以避免权限问题
    echo 请右键点击此脚本并选择"以管理员身份运行"
    echo.
    pause
)

:: 检查Python是否已安装
python --version >nul 2>&1
if %errorlevel% NEQ 0 (
    echo 错误: 未检测到Python，请确保已安装Python并添加到PATH环境变量中
    echo 您可以从 https://www.python.org/downloads/ 下载并安装Python
    pause
    exit /b 1
)

echo 已检测到Python，开始安装依赖...
echo.

echo 选择安装模式:
echo 1. 标准安装 (尝试一次性安装所有依赖)
echo 2. 逐个安装 (一个包一个包地安装，跳过失败的包)
echo 3. 使用清华镜像安装
echo 4. 使用阿里云镜像安装
echo 5. 使用所有可用镜像依次尝试 (推荐)
echo.

set /p choice=请输入选项 (1-5): 

if "%choice%"=="1" (
    echo 执行标准安装...
    python install_dependencies.py --skip-network-test
) else if "%choice%"=="2" (
    echo 执行逐个安装...
    python install_dependencies.py --one-by-one --skip-network-test
) else if "%choice%"=="3" (
    echo 使用清华镜像安装...
    python install_dependencies.py --index-url https://pypi.tuna.tsinghua.edu.cn/simple --skip-network-test
) else if "%choice%"=="4" (
    echo 使用阿里云镜像安装...
    python install_dependencies.py --index-url https://mirrors.aliyun.com/pypi/simple/ --skip-network-test
) else if "%choice%"=="5" (
    echo 使用所有可用镜像依次尝试...
    python install_dependencies.py
) else (
    echo 无效的选项，使用默认选项 5...
    python install_dependencies.py
)

echo.
echo 依赖安装过程已完成，请检查上面的输出以确认是否所有依赖都已成功安装。
echo.

:: 提示是否创建虚拟环境
echo 您是否希望创建一个虚拟环境来隔离项目依赖? (推荐)
set /p venv_choice=创建虚拟环境? (y/n): 

if /i "%venv_choice%"=="y" (
    echo 创建虚拟环境...
    python -m venv venv
    
    if %errorlevel% NEQ 0 (
        echo 创建虚拟环境失败，请确保已安装venv模块。
    ) else (
        echo 虚拟环境已创建。
        echo 使用以下命令激活虚拟环境:
        echo   Windows: venv\Scripts\activate
        echo   Linux/Mac: source venv/bin/activate
        
        :: 询问是否立即激活虚拟环境并安装依赖
        set /p activate_choice=是否立即激活虚拟环境并安装依赖? (y/n): 
        
        if /i "%activate_choice%"=="y" (
            call venv\Scripts\activate
            echo 已激活虚拟环境，开始在虚拟环境中安装依赖...
            
            :: 在虚拟环境中运行依赖安装脚本
            python install_dependencies.py
        )
    )
)

echo.
echo 安装过程已完成。
pause 