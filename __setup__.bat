@echo off

REM Kiểm tra xem môi trường ảo đã tồn tại chưa
IF EXIST .venv (
    echo Môi trường ảo virtual environment đã tồn tại.
) ELSE (
    REM Tạo mới môi trường ảo
    echo Đang tạo mới virtual environment...
    python -m venv .venv

    REM Kiểm tra việc tạo môi trường ảo có thành công không
    IF NOT EXIST .venv (
        echo Lỗi khi tạo môi trường ảo virtual environment.
        exit /b 1
    )
)

REM Kích hoạt môi trường ảo
echo Kích hoạt môi trường ảo virtual environment...
call .venv\Scripts\activate

REM Kiểm tra và xóa tệp requirements.txt nếu tồn tại
IF EXIST requirements.txt (
    echo Đang xóa tệp requirements.txt...
    del /q requirements.txt
)

REM Tạo tệp requirements.txt mới với các thư viện cần thiết
echo Khởi tạo file requirements.txt...
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
    echo passlib
    echo argon2_cffi
) > requirements.txt



REM Cài đặt và cập nhật các gói từ requirements.txt
echo Tiến hành tải packages trong requirements.txt...
pip install -U -r requirements.txt || echo Lỗi khi tải packages

echo Đã xong!
pause
