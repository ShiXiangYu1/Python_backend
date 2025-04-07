@echo off
setlocal

echo ===================================================
echo 运行单元测试
echo ===================================================

:: 设置Python环境
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo 警告: 虚拟环境未找到，使用系统Python
)

:: 检查pytest是否安装
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo 安装pytest...
    pip install pytest pytest-mock
)

:: 解析命令行参数
set VERBOSE=
set FAIL_FAST=
set TEST_PATH=tests/unit

:parse_args
if "%1"=="" goto run_tests
if "%1"=="-v" (
    set VERBOSE=-v
    shift
    goto parse_args
)
if "%1"=="-x" (
    set FAIL_FAST=-x
    shift
    goto parse_args
)
if "%1"=="-h" (
    echo 使用方法: run_unit_tests.bat [-v] [-x] [test_path]
    echo   -v  详细输出
    echo   -x  在第一个失败处停止
    echo   test_path  测试路径 (默认: tests/unit)
    exit /b 0
)
set TEST_PATH=%1
shift
goto parse_args

:run_tests
echo 运行测试: %TEST_PATH%
python tests/run_unit_tests.py %VERBOSE% %FAIL_FAST% %TEST_PATH%

:: 获取测试结果
set TEST_RESULT=%errorlevel%

:: 输出结果
if %TEST_RESULT% == 0 (
    echo.
    echo ===================================================
    echo 测试通过!
    echo ===================================================
) else (
    echo.
    echo ===================================================
    echo 测试失败，返回代码: %TEST_RESULT%
    echo ===================================================
)

exit /b %TEST_RESULT% 