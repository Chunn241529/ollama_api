#!/bin/bash

# Kiểm tra xem môi trường ảo đã tồn tại chưa
if [ -d ".venv" ]; then
    echo "Môi trường ảo virtual environment đã tồn tại."
else
    # Tạo mới môi trường ảo
    echo "Đang tạo mới virtual environment..."
    python3 -m venv .venv

    # Kiểm tra việc tạo môi trường ảo có thành công không
    if [ ! -d ".venv" ]; then
        echo "Lỗi khi tạo môi trường ảo virtual environment."
        exit 1
    fi
fi

# Kích hoạt môi trường ảo
echo "Kích hoạt môi trường ảo virtual environment..."
source .venv/bin/activate

echo "Install packed"

python3 -m pip install --upgrade pip
cat <<EOL > requirements.txt
openai
fastapi
uvicorn
python-dotenv
duckduckgo-search
requests
numpy
pillow
protobuf
tqdm
gfpgan
schedule
pygments
beautifulsoup4
python-multipart
PyJWT
httpx
aiohttp
passlib
argon2_cffi
PyPDF2
EOL

# Cài đặt và cập nhật các gói từ requirements.txt
echo "Tiến hành tải packages trong requirements.txt..."
pip install -U -r requirements.txt || echo "Lỗi khi tải packages"

echo "Đã xong!"
read -p "Nhấn Enter để tiếp tục..."
