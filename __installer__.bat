@echo off

REM Kiểm tra xem môi trường ảo đã tồn tại chưa
IF EXIST .venv (
    echo Đang xóa môi trường virtual environment hiện tại...
    rmdir /s /q .venv
)

REM Tạo lại môi trường ảo
echo Đang tạo mới virtual environment...
python -m venv .venv

REM Kiểm tra xem việc tạo môi trường ảo có thành công không
IF NOT EXIST .venv (
    echo Lỗi khi tạo môi trường ảo virtual environment.
    exit /b 1
)

REM Kích hoạt môi trường ảo
echo Kích hoạt môi trường ảo virtual environment...
call .venv\Scripts\activate

IF EXIST requirements.txt (
    rmdir /s /q requirements.txt
)

@REM REM Nâng cấp pip lên phiên bản mới nhất
@REM echo Đang cập nhật pip...
@REM python -m pip install --upgrade pip

REM Kiểm tra xem sqlite3 đã được cài đặt chưa
pip show sqlite3 > nul 2>&1
IF ERRORLEVEL 1 (
    echo sqlite3 not found. Adding to requirements.txt...
    SET ADD_SQLITE=1
) ELSE (
    echo sqlite3 already installed. Not adding to requirements.txt.
)

REM Tạo tệp requirements.txt với các thư viện cần thiết nếu chưa có
IF NOT EXIST requirements.txt (
    echo Khởi tạo file requirements.txt...
    (
        echo openai
        echo flet
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
        echo werkzeug
        echo schedule
        echo markdown
        echo pygments
        echo beautifulsoup4
        echo python-multipart
        echo jwt
        echo PyJWT
        echo langchain
        echo langchain_ollama
    ) > requirements.txt
) ELSE (
    echo requirements.txt already exists.
)

REM Cài đặt và cập nhật các gói từ requirements.txt
echo Tiến hành tải packages trong requirements.txt...
pip install -U -r requirements.txt || echo Lỗi khi tải packages

echo Đã xong!
pause
