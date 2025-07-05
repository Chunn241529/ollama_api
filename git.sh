#!/bin/bash

# Kiểm tra thông tin git user
if ! git config user.name > /dev/null || ! git config user.email > /dev/null; then
  echo "❌ Git chưa được cấu hình tên hoặc email."
  echo "Vui lòng chạy:"
  echo '  git config --global user.name "Your Name"'
  echo '  git config --global user.email "your@email.com"'
  exit 1
fi

# Lấy message commit
if [ -z "$1" ]; then
  echo "Vui lòng nhập message commit:"
  read commit_message
else
  commit_message="$1"
fi

git add .
git commit -m "$commit_message"

current_branch=$(git rev-parse --abbrev-ref HEAD)
git push origin "$current_branch"

echo "✅ Đã push lên branch '$current_branch' với message: $commit_message"
