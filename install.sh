#!/bin/bash

set -e  # Thoát ngay nếu có lỗi
set -u  # Báo lỗi nếu biến không được định nghĩa

# Thiết lập ngôn ngữ (mặc định tiếng Việt, có thể đổi sang EN qua biến LANGUAGE=EN)
LANGUAGE=${LANGUAGE:-EN}
if [ "$LANGUAGE" = "EN" ]; then
    MSG_CHECK_OS="Checking operating system..."
    MSG_OS_DETECTED="Operating system: %s (%s)"
    MSG_VENV_EXISTS="Virtual environment already exists."
    MSG_CREATE_VENV="Creating new virtual environment..."
    MSG_VENV_FAIL="Failed to create virtual environment."
    MSG_ACTIVATE_VENV="Activating virtual environment..."
    MSG_ACTIVATE_VENV_FAIL="Failed to activate virtual environment."
    MSG_CREATE_REQS="Creating requirements.txt..."
    MSG_CREATE_REQS_COMFYUI="Creating requirements-comfyui.txt..."
    MSG_INSTALL_REQS="Installing packages from requirements.txt..."
    MSG_REQS_FAIL="Failed to install packages."
    MSG_COMPLETE="Installation completed successfully!"
    MSG_SUMMARY="Installation Summary"
    MSG_PRESS_ENTER="Press Enter to continue..."
    MSG_CHECK_DEPS="Please install the following dependencies manually:"
    MSG_CURL_INSTRUCT="Install curl from: https://curl.se/download.html"
    MSG_PYTHON_INSTRUCT="Install Python 3.12 from: https://www.python.org/downloads/"
    MSG_GIT_INSTRUCT="Install git from: https://git-scm.com/downloads"
    MSG_OLLAMA_INSTRUCT="Install Ollama from: https://ollama.com/download"
    MSG_CONFIRM_DEPS="Have you installed all dependencies? (Y/N): "
    MSG_DEPS_NOT_CONFIRMED="Dependencies not confirmed. Exiting."
    MSG_DOWNLOAD_CHECKPOINT="Downloading checkpoint model..."
    MSG_CHECKPOINT_SUCCESS="Checkpoint model downloaded successfully."
    MSG_CHECKPOINT_FAIL="Failed to download checkpoint model."
    MSG_DOWNLOAD_LORAS="Downloading LoRA models..."
    MSG_LORAS_SUCCESS="LoRA models downloaded successfully."
    MSG_LORAS_FAIL="Failed to download LoRA models."
    MSG_CLONE_COMFYUI="Cloning ComfyUI repository..."
    MSG_CLONE_COMFYUI_FAIL="Failed to clone ComfyUI repository."
else
    MSG_CHECK_OS="Đang kiểm tra hệ điều hành..."
    MSG_OS_DETECTED="Hệ điều hành: %s (%s)"
    MSG_VENV_EXISTS="Môi trường ảo đã tồn tại."
    MSG_CREATE_VENV="Đang tạo mới môi trường ảo..."
    MSG_VENV_FAIL="Lỗi khi tạo môi trường ảo."
    MSG_ACTIVATE_VENV="Kích hoạt môi trường ảo..."
    MSG_ACTIVATE_VENV_FAIL="Lỗi khi kích hoạt môi trường ảo."
    MSG_CREATE_REQS="Tạo file requirements.txt..."
    MSG_CREATE_REQS_COMFYUI="Tạo file requirements-comfyui.txt..."
    MSG_INSTALL_REQS="Cài đặt các gói từ requirements.txt..."
    MSG_REQS_FAIL="Lỗi khi cài đặt các gói."
    MSG_COMPLETE="Cài đặt hoàn tất!"
    MSG_SUMMARY="Tóm tắt cài đặt"
    MSG_PRESS_ENTER="Nhấn Enter để thoát..."
    MSG_CHECK_DEPS="Vui lòng cài đặt công cụ sau:"
    MSG_CURL_INSTRUCT="Cài đặt curl từ: https://curl.se/download.html"
    MSG_PYTHON_INSTRUCT="Cài đặt Python 3.12 từ: https://www.python.org/downloads/"
    MSG_GIT_INSTRUCT="Cài đặt git từ: https://git-scm.com/downloads"
    MSG_OLLAMA_INSTRUCT="Cài đặt Ollama từ: https://ollama.com/download"
    MSG_CONFIRM_DEPS="Xác nhận đã cài (Y/N): "
    MSG_DEPS_NOT_CONFIRMED="Phụ thuộc chưa được xác nhận. Thoát."
    MSG_DOWNLOAD_CHECKPOINT="Đang tải checkpoint model..."
    MSG_CHECKPOINT_SUCCESS="Tải checkpoint model thành công."
    MSG_CHECKPOINT_FAIL="Không thể tải checkpoint model."
    MSG_DOWNLOAD_LORAS="Đang tải LoRA models..."
    MSG_LORAS_SUCCESS="Tải LoRA models thành công."
    MSG_LORAS_FAIL="Không thể tải LoRA models."
    MSG_CLONE_COMFYUI="Clone kho lưu trữ ComfyUI..."
    MSG_CLONE_COMFYUI_FAIL="Lỗi khi clone kho lưu trữ ComfyUI."
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
LOG_FILE="install_$(date +%Y%m%d_%H%M%S).log"
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

# Tóm tắt trạng thái
SUMMARY=()

# Kiểm tra hệ điều hành
check_os() {
    show_progress "$MSG_CHECK_OS" 10
    OS=$(uname -s)
    ARCH=$(uname -m)
    log_info "$(printf "$MSG_OS_DETECTED" "$OS" "$ARCH")"
    SUMMARY+=("OS Check: ${GREEN}${CHECKMARK}${NC}")
}

# Hiển thị hướng dẫn cài đặt phụ thuộc
check_dependencies() {
    echo -e "${YELLOW}${MSG_CHECK_DEPS}${NC}" >&3
    echo -e "${BLUE}│${NC} $MSG_CURL_INSTRUCT" >&3
    echo -e "${BLUE}│${NC} $MSG_PYTHON_INSTRUCT" >&3
    echo -e "${BLUE}│${NC} $MSG_GIT_INSTRUCT" >&3
    echo -e "${BLUE}│${NC} $MSG_OLLAMA_INSTRUCT" >&3
    echo -e "${BLUE} ${NC} $MSG_CONFIRM_DEPS" >&3
    read -r response
    if [[ "$response" != "Y" && "$response" != "y" ]]; then
        log_error "$MSG_DEPS_NOT_CONFIRMED"
    fi
    # Verify dependencies
    if ! command -v curl >/dev/null 2>&1; then
        log_error "curl not found. Please install curl from https://curl.se/download.html"
    fi
    if ! command -v python3.12 >/dev/null 2>&1; then
        log_error "Python 3.12 not found. Please install Python 3.12 from https://www.python.org/downloads/"
    fi
    if ! command -v git >/dev/null 2>&1; then
        log_error "git not found. Please install git from https://git-scm.com/downloads"
    fi
    if ! command -v ollama >/dev/null 2>&1; then
        log_error "Ollama not found. Please install Ollama from https://ollama.com/download"
    fi
    log_info "All dependencies confirmed."
    SUMMARY+=("Dependencies: ${GREEN}${CHECKMARK}${NC}")
}

# Kiểm tra môi trường ảo
check_venv() {
    if [ -d ".venv" ]; then
        log_info "$MSG_VENV_EXISTS"
        SUMMARY+=("Virtual Env: ${GREEN}${CHECKMARK}${NC}")
    else
        show_progress "$MSG_CREATE_VENV" 15
        python3.12 -m venv .venv || { log_error "$MSG_VENV_FAIL"; SUMMARY+=("Virtual Env: ${RED}${CROSS}${NC}"); }
        log_info "$MSG_CREATE_VENV"
        SUMMARY+=("Virtual Env: ${GREEN}${CHECKMARK}${NC}")
    fi
}

# Kích hoạt môi trường ảo
activate_venv() {
    show_progress "$MSG_ACTIVATE_VENV" 10
    source .venv/bin/activate || { log_error "$MSG_ACTIVATE_VENV_FAIL"; SUMMARY+=("Activate Venv: ${RED}${CROSS}${NC}"); }
    log_info "$MSG_ACTIVATE_VENV"
    SUMMARY+=("Activate Venv: ${GREEN}${CHECKMARK}${NC}")
}

# Tạo file requirements.txt
create_requirements() {
    show_progress "$MSG_CREATE_REQS" 10
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
passlib[argon2]
argon2-cffi
PyPDF2
websocket-client
requests
transformers
soundfile
accelerate
rich
prompt_toolkit
reportlab
textual
EOL
    log_info "$MSG_CREATE_REQS"
    SUMMARY+=("Requirements.txt: ${GREEN}${CHECKMARK}${NC}")
}

# Cài đặt các gói
install_packages() {
    show_progress "$MSG_INSTALL_REQS" 30
    pip install -U -r requirements.txt || { log_error "$MSG_REQS_FAIL"; SUMMARY+=("Packages: ${RED}${CROSS}${NC}"); }
    log_info "$MSG_INSTALL_REQS"
    SUMMARY+=("Packages: ${GREEN}${CHECKMARK}${NC}")
}

# Hàm hiển thị tóm tắt
show_summary() {
    for item in "${SUMMARY[@]}"; do
        echo -e "${BLUE}│${NC} $item" >&3
    done
    echo -e "${GREEN}${CHECKMARK} $MSG_COMPLETE${NC}" >&3
    # Xóa file log
    if [ -f "$LOG_FILE" ]; then
        rm -f "$LOG_FILE"
    fi
    # Xóa file requirements.txt
    if [ -f "requirements.txt" ]; then
        rm -f "requirements.txt"
    fi
}

# Thực thi các bước
check_os
check_dependencies
check_venv
activate_venv
create_requirements
install_packages
show_summary

echo -e "$MSG_PRESS_ENTER" >&3
read -r
