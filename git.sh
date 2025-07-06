#!/bin/bash

# Kiểm tra cấu hình Git
if ! git config user.name > /dev/null || ! git config user.email > /dev/null; then
  echo "❌ Git chưa cấu hình tên hoặc email."
  echo "Vui lòng chạy:"
  echo '  git config --global user.name "Your Name"'
  echo '  git config --global user.email "your@email.com"'
  exit 1
fi

# Lấy commit message
if [ -z "$1" ]; then
  echo "📝 Nhập commit message:"
  read commit_message
else
  commit_message="$1"
fi

# Add file
git add .

# Commit
git commit -m "$commit_message"

# Hiển thị danh sách branch
echo "🌿 Các branch hiện tại:"
git branch

# Hỏi chọn branch
echo "🔀 Nhập tên branch bạn muốn push lên (để trống để dùng branch hiện tại):"
read selected_branch

# Nếu để trống, dùng branch hiện tại
if [ -z "$selected_branch" ]; then
  selected_branch=$(git rev-parse --abbrev-ref HEAD)
fi

# Push
git push origin "$selected_branch"

echo "✅ Đã push lên branch '$selected_branch' với message: $commit_message"
