#!/bin/bash

set -e  # Thoát ngay nếu có lỗi
set -u  # Báo lỗi nếu biến không được định nghĩa

# Thiết lập ngôn ngữ (mặc định tiếng Việt, có thể đổi sang EN qua biến LANGUAGE=EN)
LANGUAGE=${LANGUAGE:-VN}
if [ "$LANGUAGE" = "EN" ]; then
    MSG_CHECK_OS="Checking operating system..."
    MSG_OS_DETECTED="Operating system: %s (%s)"
    MSG_CHECK_PYTHON="Checking for Python 3.12..."
    MSG_PYTHON_FOUND="Python 3.12 already installed."
    MSG_PYTHON_NOT_FOUND="Python 3.12 not found. Installing..."
    MSG_INSTALL_PYTHON_DEBIAN="Installing Python 3.12 on Debian/Ubuntu..."
    MSG_INSTALL_PYTHON_CENTOS="Installing Python 3.12 on CentOS/RHEL..."
    MSG_INSTALL_PYTHON_MAC="Installing Python 3.12 on macOS via Homebrew..."
    MSG_PYTHON_SUCCESS="Python 3.12 installed successfully."
    MSG_PYTHON_FAIL="Failed to install Python 3.12."
    MSG_VENV_EXISTS="Virtual environment already exists."
    MSG_CREATE_VENV="Creating new virtual environment..."
    MSG_VENV_FAIL="Failed to create virtual environment."
    MSG_ACTIVATE_VENV="Activating virtual environment..."
    MSG_ACTIVATE_VENV_FAIL="Failed to activate virtual environment."
    MSG_UPDATE_PIP="Updating pip..."
    MSG_PIP_FAIL="Failed to update pip."
    MSG_CREATE_REQS="Creating requirements.txt..."
    MSG_CREATE_REQS_COMFYUI="Creating requirements-comfyui.txt..."
    MSG_INSTALL_REQS="Installing packages from requirements.txt..."
    MSG_REQS_FAIL="Failed to install packages."
    MSG_COMPLETE="Installation completed successfully!"
    MSG_SUMMARY="Installation Summary"
    MSG_PRESS_ENTER="Press Enter to continue..."
    MSG_CHECK_GIT="Checking for Git..."
    MSG_GIT_FOUND="Git already installed."
    MSG_GIT_NOT_FOUND="Git not found. Installing..."
    MSG_INSTALL_GIT_DEBIAN="Installing Git on Debian/Ubuntu..."
    MSG_INSTALL_GIT_CENTOS="Installing Git on CentOS/RHEL..."
    MSG_INSTALL_GIT_MAC="Installing Git on macOS via Homebrew..."
    MSG_GIT_SUCCESS="Git installed successfully."
    MSG_GIT_FAIL="Failed to install Git."
    MSG_CLONE_COMFYUI="Cloning ComfyUI repository..."
    MSG_CLONE_COMFYUI_FAIL="Failed to clone ComfyUI repository."
else
    MSG_CHECK_OS="Đang kiểm tra hệ điều hành..."
    MSG_OS_DETECTED="Hệ điều hành: %s (%s)"
    MSG_CHECK_PYTHON="Đang kiểm tra Python 3.12..."
    MSG_PYTHON_FOUND="Python 3.12 đã được cài đặt."
    MSG_PYTHON_NOT_FOUND="Python 3.12 không được tìm thấy. Đang tiến hành cài đặt..."
    MSG_INSTALL_PYTHON_DEBIAN="Cài đặt Python 3.12 trên Debian/Ubuntu..."
    MSG_INSTALL_PYTHON_CENTOS="Cài đặt Python 3.12 trên CentOS/RHEL..."
    MSG_INSTALL_PYTHON_MAC="Cài đặt Python 3.12 trên macOS qua Homebrew..."
    MSG_PYTHON_SUCCESS="Cài đặt Python 3.12 thành công."
    MSG_PYTHON_FAIL="Không thể cài đặt Python 3.12."
    MSG_VENV_EXISTS="Môi trường ảo đã tồn tại."
    MSG_CREATE_VENV="Đang tạo mới môi trường ảo..."
    MSG_VENV_FAIL="Lỗi khi tạo môi trường ảo."
    MSG_ACTIVATE_VENV="Kích hoạt môi trường ảo..."
    MSG_ACTIVATE_VENV_FAIL="Lỗi khi kích hoạt môi trường ảo."
    MSG_UPDATE_PIP="Cập nhật pip..."
    MSG_PIP_FAIL="Lỗi khi cập nhật pip."
    MSG_CREATE_REQS="Tạo file requirements.txt..."
    MSG_CREATE_REQS_COMFYUI="Tạo file requirements-comfyui.txt..."
    MSG_INSTALL_REQS="Cài đặt các gói từ requirements.txt..."
    MSG_REQS_FAIL="Lỗi khi cài đặt các gói."
    MSG_COMPLETE="Cài đặt hoàn tất!"
    MSG_SUMMARY="Tóm tắt cài đặt"
    MSG_PRESS_ENTER="Nhấn Enter để thoát..."
    MSG_CHECK_GIT="Đang kiểm tra Git..."
    MSG_GIT_FOUND="Git đã được cài đặt."
    MSG_GIT_NOT_FOUND="Git không được tìm thấy. Đang tiến hành cài đặt..."
    MSG_INSTALL_GIT_DEBIAN="Cài đặt Git trên Debian/Ubuntu..."
    MSG_INSTALL_GIT_CENTOS="Cài đặt Git trên CentOS/RHEL..."
    MSG_INSTALL_GIT_MAC="Cài đặt Git trên macOS qua Homebrew..."
    MSG_GIT_SUCCESS="Cài đặt Git thành công."
    MSG_GIT_FAIL="Không thể cài đặt Git."
    MSG_CLONE_COMFYUI="Đang clone kho lưu trữ ComfyUI..."
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

# Kiểm tra và cài đặt công cụ phụ thuộc
check_dependencies() {
    show_progress "$MSG_CHECK_OS" 10

    # Kiểm tra và cài đặt Git
    show_progress "$MSG_CHECK_GIT" 10
    if command -v git >/dev/null 2>&1; then
        log_info "$MSG_GIT_FOUND"
        SUMMARY+=("Git: ${GREEN}${CHECKMARK}${NC}")
    else
        log_warn "$MSG_GIT_NOT_FOUND"
        show_progress "$MSG_GIT_NOT_FOUND" 20
        case "$OS" in
            Linux)
                if command -v apt-get >/dev/null 2>&1; then
                    log_info "$MSG_INSTALL_GIT_DEBIAN"
                    show_progress "$MSG_INSTALL_GIT_DEBIAN" 30
                    sudo apt-get update
                    sudo apt-get install -y git
                elif command -v yum >/dev/null 2>&1; then
                    log_info "$MSG_INSTALL_GIT_CENTOS"
                    show_progress "$MSG_INSTALL_GIT_CENTOS" 30
                    sudo yum install -y git
                else
                    log_error "Hệ thống Linux không hỗ trợ (không tìm thấy apt hoặc yum)."
                fi
                ;;
            Darwin)
                if command -v brew >/dev/null 2>&1; then
                    log_info "$MSG_INSTALL_GIT_MAC"
                    show_progress "$MSG_INSTALL_GIT_MAC" 30
                    brew install git
                else
                    log_error "Homebrew không được cài đặt. Vui lòng cài Homebrew trước: https://brew.sh/"
                fi
                ;;
            *)
                log_error "Hệ điều hành không được hỗ trợ: $OS"
                ;;
        esac
        if command -v git >/dev/null 2>&1; then
            log_info "$MSG_GIT_SUCCESS"
            SUMMARY+=("Git: ${GREEN}${CHECKMARK}${NC}")
        else
            log_error "$MSG_GIT_FAIL"
            SUMMARY+=("Git: ${RED}${CROSS}${NC}")
        fi
    fi

    # Kiểm tra curl
    if ! command -v curl >/dev/null 2>&1; then
        log_error "Công cụ curl không được tìm thấy. Vui lòng cài đặt trước khi tiếp tục."
    fi
    SUMMARY+=("Dependencies: ${GREEN}${CHECKMARK}${NC}")
}

# Kiểm tra hệ điều hành
OS=$(uname -s)
ARCH=$(uname -m)
log_info "$(printf "$MSG_OS_DETECTED" "$OS" "$ARCH")"

# Hàm kiểm tra và cài đặt Python 3.12
install_python() {
    show_progress "$MSG_CHECK_PYTHON" 10
    if command -v python3.12 >/dev/null 2>&1; then
        log_info "$MSG_PYTHON_FOUND"
        PYTHON_CMD="python3.12"
        SUMMARY+=("Python 3.12: ${GREEN}${CHECKMARK}${NC}")
        return 0
    fi

    log_warn "$MSG_PYTHON_NOT_FOUND"
    show_progress "$MSG_PYTHON_NOT_FOUND" 20

    case "$OS" in
        Linux)
            if command -v apt-get >/dev/null 2>&1; then
                log_info "$MSG_INSTALL_PYTHON_DEBIAN"
                show_progress "$MSG_INSTALL_PYTHON_DEBIAN" 30
                sudo apt-get update
                sudo apt-get install -y software-properties-common
                sudo add-apt-repository -y ppa:deadsnakes/ppa
                sudo apt-get update
                sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
            elif command -v yum >/dev/null 2>&1; then
                log_info "$MSG_INSTALL_PYTHON_CENTOS"
                show_progress "$MSG_INSTALL_PYTHON_CENTOS" 30
                sudo yum install -y epel-release
                sudo yum install -y python3.12
            else
                log_error "Hệ thống Linux không hỗ trợ (không tìm thấy apt hoặc yum)."
            fi
            ;;
        Darwin)
            if command -v brew >/dev/null 2>&1; then
                log_info "$MSG_INSTALL_PYTHON_MAC"
                show_progress "$MSG_INSTALL_PYTHON_MAC" 30
                brew install python@3.12
            else
                log_error "Homebrew không được cài đặt. Vui lòng cài Homebrew trước: https://brew.sh/"
            fi
            ;;
        *)
            log_error "Hệ điều hành không được hỗ trợ: $OS"
            ;;
    esac

    if command -v python3.12 >/dev/null 2>&1; then
        PYTHON_CMD="python3.12"
        log_info "$MSG_PYTHON_SUCCESS"
        SUMMARY+=("Python 3.12: ${GREEN}${CHECKMARK}${NC}")
    else
        log_error "$MSG_PYTHON_FAIL"
        SUMMARY+=("Python 3.12: ${RED}${CROSS}${NC}")
    fi
}

# Kiểm tra môi trường ảo
check_venv() {
    if [ -d ".venv" ]; then
        log_info "$MSG_VENV_EXISTS"
        SUMMARY+=("Virtual Env: ${GREEN}${CHECKMARK}${NC}")
    else
        show_progress "$MSG_CREATE_VENV" 15
        "$PYTHON_CMD" -m venv .venv || { log_error "$MSG_VENV_FAIL"; SUMMARY+=("Virtual Env: ${RED}${CROSS}${NC}"); }
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

# Cập nhật pip
update_pip() {
    show_progress "$MSG_UPDATE_PIP" 15
    python -m pip install --upgrade pip || { log_error "$MSG_PIP_FAIL"; SUMMARY+=("Update pip: ${RED}${CROSS}${NC}"); }
    log_info "$MSG_UPDATE_PIP"
    SUMMARY+=("Update pip: ${GREEN}${CHECKMARK}${NC}")
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
selenium
webdriver-manager
textual
EOL
    log_info "$MSG_CREATE_REQS"
    SUMMARY+=("Requirements.txt: ${GREEN}${CHECKMARK}${NC}")
}

create_requirements_comfyui() {
    show_progress "$MSG_CREATE_REQS_COMFYUI" 10
    cat <<EOL > requirements-comfyui.txt
comfyui-frontend-package==1.21.7
comfyui-workflow-templates==0.1.25
comfyui-embedded-docs==0.2.0
torch
torchsde
torchvision
torchaudio
numpy>=1.25.0
einops
transformers>=4.28.1
tokenizers>=0.13.3
sentencepiece
safetensors>=0.4.2
aiohttp>=3.11.8
yarl>=1.18.0
pyyaml
Pillow
scipy
tqdm
psutil
kornia>=0.7.1
spandrel
soundfile
av>=14.2.0
pydantic~=2.0
EOL
    log_info "$MSG_CREATE_REQS_COMFYUI"
    SUMMARY+=("Requirements-Comfyui.txt: ${GREEN}${CHECKMARK}${NC}")
}

# Cài đặt các gói
install_packages() {
    # Clone ComfyUI repository
    show_progress "$MSG_CLONE_COMFYUI" 20
    mkdir -p modules
    cd modules
    if [ -d "ComfyUI" ]; then
        log_info "ComfyUI repository already exists."
        SUMMARY+=("ComfyUI Clone: ${GREEN}${CHECKMARK}${NC}")
    else
        git clone https://github.com/comfyanonymous/ComfyUI.git || { log_error "$MSG_CLONE_COMFYUI_FAIL"; SUMMARY+=("ComfyUI Clone: ${RED}${CROSS}${NC}"); }
        log_info "$MSG_CLONE_COMFYUI"
        SUMMARY+=("ComfyUI Clone: ${GREEN}${CHECKMARK}${NC}")
    fi
    cd ..

    # Install packages
    show_progress "$MSG_INSTALL_REQS" 30
    pip install -U -r requirements.txt || { log_error "$MSG_REQS_FAIL"; SUMMARY+=("Packages: ${RED}${CROSS}${NC}"); }
    log_info "Cài đặt PyTorch..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
    pip install -U -r requirements-comfyui.txt || { log_error "$MSG_REQS_FAIL"; SUMMARY+=("Packages: ${RED}${CROSS}${NC}"); }
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
    if [ -f "requirements-comfyui.txt" ]; then
        rm -f "requirements-comfyui.txt"
    fi
}

# Thực thi các bước
check_dependencies
install_python
check_venv
activate_venv
update_pip
create_requirements
create_requirements_comfyui
install_packages
show_summary

echo -e "$MSG_PRESS_ENTER" >&3
read -r
