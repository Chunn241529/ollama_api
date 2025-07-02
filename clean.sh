#!/bin/bash

# Đặt mã hóa UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Thiết lập ngôn ngữ (mặc định tiếng Việt, có thể đổi sang EN qua biến LANGUAGE=EN)
LANGUAGE=${LANGUAGE:-VN}
if [ "$LANGUAGE" = "EN" ]; then

    MSG_CANCEL="Operation canceled."
    MSG_CLEANING="Cleaning cache..."
    MSG_CLEAN_HF="Clearing Hugging Face cache..."
    MSG_CLEAN_SNAP="Clearing snap code cache..."
    MSG_CLEAN_PYCACHE="Clearing __pycache__ directories..."
    MSG_CLEAN_PYC="Clearing *.pyc files..."
    MSG_CLEAN_PIP="Clearing pip cache..."
    MSG_CLEAN_TORCH="Clearing PyTorch cache..."
    MSG_CLEAN_COMFYUI="Clearing ComfyUI cache..."
    MSG_SUCCESS="All caches cleared successfully."
    MSG_LOG="Logs saved to: %s"
else

    MSG_CANCEL="Hủy thao tác."
    MSG_CLEANING="Dọn dẹp cache..."
    MSG_CLEAN_HF="Xóa cache Hugging Face..."
    MSG_CLEAN_SNAP="Xóa cache snap code..."
    MSG_CLEAN_PYCACHE="Xóa các thư mục __pycache__..."
    MSG_CLEAN_PYC="Xóa các file *.pyc..."
    MSG_CLEAN_PIP="Xóa cache pip..."
    MSG_CLEAN_TORCH="Xóa cache PyTorch..."
    MSG_CLEAN_COMFYUI="Xóa cache ComfyUI..."
    MSG_SUCCESS="Đã xóa toàn bộ cache thành công."
    MSG_LOG="Log được lưu tại: %s"
fi

# Màu sắc và biểu tượng
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m'
CHECKMARK="✔"
CROSS="✖"
SPINNER=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")

# File log
LOG_FILE="clean_cache_$(date +%Y%m%d_%H%M%S).log"
exec 3>&1 1>>"$LOG_FILE" 2>&1

# Hàm hiển thị thông báo
log_info() { echo -e "${GREEN}${CHECKMARK} $1${NC}" >&3; echo "[INFO] $1" >> "$LOG_FILE"; }
log_warn() { echo -e "${YELLOW}! $1${NC}" >&3; echo "[WARN] $1" >> "$LOG_FILE"; }
log_error() { echo -e "${RED}${CROSS} $1${NC}" >&3; echo "[ERROR] $1" >> "$LOG_FILE"; exit 1; }

# Hàm hiển thị thanh tiến trình
show_progress() {
    local msg=$1
    local duration=$2
    local i=0
    while [ $i -lt $duration ]; do
        printf "\r${BLUE}%s %s${NC}" "$msg" "${SPINNER[$((i % 10))]}" >&3
        sleep 0.1
        i=$((i + 1))
    done
    printf "\r\033[K" >&3  # Xóa dòng spinner
}



# Bắt đầu dọn dẹp
log_info "$MSG_CLEANING"

# Xóa cache Hugging Face
show_progress "$MSG_CLEAN_HF" 10
if [ -d ~/.cache/huggingface ]; then
    rm -rf ~/.cache/huggingface/* || log_error "Không thể xóa cache Hugging Face."
    log_info "$MSG_CLEAN_HF"
else
    log_warn "Không tìm thấy thư mục cache Hugging Face."
fi

# Xóa các thư mục __pycache__
show_progress "$MSG_CLEAN_PYCACHE" 15
find "$PWD" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || log_warn "Không thể xóa một số thư mục __pycache__."
log_info "$MSG_CLEAN_PYCACHE"

# Xóa các file *.pyc
show_progress "$MSG_CLEAN_PYC" 15
find "$PWD" -type f -name "*.pyc" -exec rm -f {} + 2>/dev/null || log_warn "Không thể xóa một số file *.pyc."
log_info "$MSG_CLEAN_PYC"


# Xóa cache pip
show_progress "$MSG_CLEAN_PIP" 10
if [ -d ~/.cache/pip ]; then
    rm -rf ~/.cache/pip/* || log_error "Không thể xóa cache pip."
    log_info "$MSG_CLEAN_PIP"
else
    log_warn "Không tìm thấy thư mục cache pip."
fi

# Xóa cache hệ thống Linux phổ biến
show_progress "Xóa cache hệ thống Linux..." 10
# Xóa cache apt (Debian/Ubuntu)
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get clean && log_info "Đã xóa cache apt-get." || log_warn "Không thể xóa cache apt-get."
fi
# Xóa cache dnf (Fedora)
if command -v dnf >/dev/null 2>&1; then
    sudo dnf clean all && log_info "Đã xóa cache dnf." || log_warn "Không thể xóa cache dnf."
fi
# Xóa cache yum (CentOS/RHEL)
if command -v yum >/dev/null 2>&1; then
    sudo yum clean all && log_info "Đã xóa cache yum." || log_warn "Không thể xóa cache yum."
fi
# Xóa cache pacman (Arch Linux)
if command -v pacman >/dev/null 2>&1; then
    sudo pacman -Scc --noconfirm && log_info "Đã xóa cache pacman." || log_warn "Không thể xóa cache pacman."
fi
# Xóa cache systemd journal (nếu có)
if command -v journalctl >/dev/null 2>&1; then
    sudo journalctl --vacuum-time=2d && log_info "Đã dọn dẹp journalctl (giữ lại 2 ngày)." || log_warn "Không thể dọn dẹp journalctl."
fi
# Xóa cache thumbnail (nếu có)
if [ -d ~/.cache/thumbnails ]; then
    rm -rf ~/.cache/thumbnails/* && log_info "Đã xóa cache thumbnails." || log_warn "Không thể xóa cache thumbnails."
fi



# Hoàn tất
log_info "$MSG_SUCCESS"
log_info "$(printf "$MSG_LOG" "$LOG_FILE")"

# Xóa log sau 4 giây
sleep 4
rm -f "$LOG_FILE"
