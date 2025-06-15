#!/bin/bash

# Đặt mã hóa UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

echo "CẢNH BÁO: Script này sẽ xóa toàn bộ các file __pycache__ và *.pyc trong thư mục root."
echo "Hành động này không thể hoàn tác. Bạn có chắc chắn muốn tiếp tục? (y/N)"
read -r confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Hủy thao tác."
    exit 1
fi

echo "Đang tìm và xóa các tệp j97..."

cd ~/.cache/huggingface/
ls
rm -rf ~/.cache/huggingface/*
echo "clear huggingface cache - done"

rm -rf /home/nguyentrung/snap/code/184/.local/share/Trash/files/*
echo "clear snap code cache - done"

# Tìm và xóa các thư mục __pycache__
find / -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Tìm và xóa các file *.pyc
find / -type f -name "*.pyc" -exec rm -f {} + 2>/dev/null

echo "Đã xóa toàn bộ cache Python thành công."
