@echo off
setlocal enabledelayedexpansion

:: Thiết lập ngôn ngữ (mặc định tiếng Việt, đổi thành EN bằng biến LANGUAGE=EN)
if "%LANGUAGE%"=="" set "LANGUAGE=VN"
if /i "%LANGUAGE%"=="EN" (
    set "MSG_CHECK_OS=Checking operating system..."
    set "MSG_OS_DETECTED=Operating system: Windows (x86/x64)"
    set "MSG_CHECK_PYTHON=Checking for Python 3.12..."
    set "MSG_PYTHON_FOUND=Python 3.12 already installed."
    set "MSG_PYTHON_NOT_FOUND=Python 3.12 not found. Please install it manually."
    set "MSG_VENV_EXISTS=Virtual environment already exists."
    set "MSG_CREATE_VENV=Creating new virtual environment..."
    set "MSG_VENV_FAIL=Failed to create virtual environment."
    set "MSG_ACTIVATE_VENV=Activating virtual environment..."
    set "MSG_ACTIVATE_VENV_FAIL=Failed to activate virtual environment."
    set "MSG_UPDATE_PIP=Updating pip..."
    set "MSG_PIP_FAIL=Failed to update pip."
    set "MSG_CREATE_REQS=Creating requirements.txt..."
    set "MSG_INSTALL_REQS=Installing packages from requirements.txt..."
    set "MSG_REQS_FAIL=Failed to install packages."
    set "MSG_COMPLETE=Installation completed successfully!"
    set "MSG_SUMMARY=Installation Summary"
    set "MSG_PRESS_ENTER=Press Enter to continue..."
) else (
    set "MSG_CHECK_OS=Đang kiểm tra hệ điều hành..."
    set "MSG_OS_DETECTED=Hệ điều hành: Windows (x86/x64)"
    set "MSG_CHECK_PYTHON=Đang kiểm tra Python 3.12..."
    set "MSG_PYTHON_FOUND=Python 3.12 đã được cài đặt."
    set "MSG_PYTHON_NOT_FOUND=Python 3.12 không được tìm thấy. Vui lòng cài đặt thủ công."
    set "MSG_VENV_EXISTS=Môi trường ảo đã tồn tại."
    set "MSG_CREATE_VENV=Đang tạo mới môi trường ảo..."
    set "MSG_VENV_FAIL=Lỗi khi tạo môi trường ảo."
    set "MSG_ACTIVATE_VENV=Kích hoạt môi trường ảo..."
    set "MSG_ACTIVATE_VENV_FAIL=Lỗi khi kích hoạt môi trường ảo."
    set "MSG_UPDATE_PIP=Cập nhật pip..."
    set "MSG_PIP_FAIL=Lỗi khi cập nhật pip."
    set "MSG_CREATE_REQS=Tạo file requirements.txt..."
    set "MSG_INSTALL_REQS=Cài đặt các gói từ requirements.txt..."
    set "MSG_REQS_FAIL=Lỗi khi cài đặt các gói."
    set "MSG_COMPLETE=Cài đặt hoàn tất!"
    set "MSG_SUMMARY=Tóm tắt cài đặt"
    set "MSG_PRESS_ENTER=Nhấn Enter để thoát..."
)

:: Tạo file log
set "LOG_FILE=install_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
call :LogInfo "[INFO] Bắt đầu ghi log vào %LOG_FILE%"

:: Hàm kiểm tra công cụ phụ thuộc
call :CheckDependencies
if errorlevel 1 exit /b 1

:: Kiểm tra Python
call :CheckPython
if errorlevel 1 exit /b 1

:: Kiểm tra môi trường ảo
call :CheckVenv
if errorlevel 1 exit /b 1

:: Kích hoạt môi trường ảo
call :ActivateVenv
if errorlevel 1 exit /b 1

:: Cập nhật pip
call :UpdatePip
if errorlevel 1 exit /b 1

:: Tạo requirements.txt
call :CreateRequirements
if errorlevel 1 exit /b 1

:: Cài đặt các gói
call :InstallPackages
if errorlevel 1 exit /b 1

:: Hiển thị tóm tắt
call :ShowSummary

:: Kết thúc
echo.
echo !MSG_PRESS_ENTER!
pause >nul
exit /b 0

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Các hàm con
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:CheckDependencies
    echo.
    call :ShowProgress "%MSG_CHECK_OS%" 10
    :: Kiểm tra curl và git (tùy chọn)
    where curl git >nul 2>&1
    if errorlevel 1 (
        echo.
        echo [WARN] Một số công cụ không được tìm thấy (curl/git). Vui lòng cài đặt nếu cần.
    )
    call :LogInfo "[INFO] Dependencies: OK"
    exit /b 0

:CheckPython
    echo.
    call :ShowProgress "%MSG_CHECK_PYTHON%" 10
    python --version 2>nul | findstr "3.12" >nul
    if not errorlevel 1 (
        call :LogInfo "[INFO] %MSG_PYTHON_FOUND%"
        set "PYTHON_CMD=python"
        exit /b 0
    )
    call :LogWarn "[WARN] %MSG_PYTHON_NOT_FOUND%"
    exit /b 1

:CheckVenv
    echo.
    if exist ".venv" (
        call :LogInfo "[INFO] %MSG_VENV_EXISTS%"
        exit /b 0
    )
    call :ShowProgress "%MSG_CREATE_VENV%" 15
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        call :LogError "[ERROR] %MSG_VENV_FAIL%"
        exit /b 1
    )
    call :LogInfo "[INFO] %MSG_CREATE_VENV%"
    exit /b 0

:ActivateVenv
    echo.
    call :ShowProgress "%MSG_ACTIVATE_VENV%" 10
    call .venv\Scripts\activate.bat
    if errorlevel 1 (
        call :LogError "[ERROR] %MSG_ACTIVATE_VENV_FAIL%"
        exit /b 1
    )
    call :LogInfo "[INFO] %MSG_ACTIVATE_VENV%"
    exit /b 0

:UpdatePip
    echo.
    call :ShowProgress "%MSG_UPDATE_PIP%" 15
    pip install --upgrade pip >nul
    if errorlevel 1 (
        call :LogError "[ERROR] %MSG_PIP_FAIL%"
        exit /b 1
    )
    call :LogInfo "[INFO] %MSG_UPDATE_PIP%"
    exit /b 0

:CreateRequirements
    echo.
    call :ShowProgress "%MSG_CREATE_REQS%" 10
    (
        echo openai
        echo fastapi
        echo uvicorn
        echo python-dotenv
        echo duckduckgo-search
        echo requests
        echo numpy
        echo pillow
        echo protobuf
        echo tqdm
        echo gfpgan
        echo schedule
        echo pygments
        echo beautifulsoup4
        echo python-multipart
        echo PyJWT
        echo httpx
        echo aiohttp
        echo passlib[argon2]
        echo argon2-cffi
        echo PyPDF2
        echo websocket-client
        echo transformers
        echo qwen_omni_utils
        echo soundfile
        echo accelerate
    ) > requirements.txt
    call :LogInfo "[INFO] %MSG_CREATE_REQS%"
    exit /b 0

:InstallPackages
    echo.
    call :ShowProgress "%MSG_INSTALL_REQS%" 30
    pip install -U -r requirements.txt >nul
    if errorlevel 1 (
        call :LogError "[ERROR] %MSG_REQS_FAIL%"
        exit /b 1
    )
    call :LogInfo "[INFO] %MSG_INSTALL_REQS%"
    exit /b 0

:ShowSummary
    echo.
    echo %MSG_SUMMARY%
    echo -------------------------------
    echo - Python: OK
    echo - Virtual Env: OK
    echo - Pip: OK
    echo - Requirements: OK
    echo -------------------------------
    echo %MSG_COMPLETE%
    del /q "%LOG_FILE%" >nul 2>&1
    del /q "requirements.txt" >nul 2>&1
    exit /b 0

:ShowProgress
    set "msg=%~1"
    set "duration=%~2"
    set "spinner=|/-\\"
    for /l %%i in (1,1,%duration%) do (
        for /l %%j in (0,1,3) do (
            <nul set /p ".=%msg% !spinner:~%%j,1!  "
            timeout /t 1 /nobreak >nul
            <nul set /p ".=    \r"
        )
    )
    exit /b 0

:LogInfo
    echo %~1
    echo %~1 >> "%LOG_FILE%"
    exit /b 0

:LogWarn
    echo [WARN] %~1
    echo [WARN] %~1 >> "%LOG_FILE%"
    exit /b 0

:LogError
    echo [ERROR] %~1
    echo [ERROR] %~1 >> "%LOG_FILE%"
    exit /b 1
