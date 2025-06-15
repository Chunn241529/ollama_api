#!/bin/bash
# Script cài đặt môi trường Python 3.12 và các thư viện cần thiết cho Linux/macOS
# Mục đích: Tự động hóa việc cài đặt Python 3.12, tạo môi trường ảo, và cài đặt các thư viện
# Yêu cầu: Quyền quản trị (sudo) trên Linux, Homebrew trên macOS (tùy chọn)
# Hướng dẫn: Chạy script bằng lệnh `bash install.sh`

set -e  # Thoát khi có lỗi
set -u  # Báo lỗi khi sử dụng biến chưa khai báo

# Biến cấu hình
VENV_DIR=".venv"
PYTHON_VERSION="3.12"
REQUIREMENTS_FILE="requirements.txt"
COMFYUI_REQUIREMENTS="requirements-comfyui.txt"

# Hàm ghi log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
}

# Hàm ghi lỗi và thoát
log_error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# Kiểm tra quyền sudo
check_sudo() {
    if ! command -v sudo &> /dev/null; then
        log_error "sudo không được cài đặt. Vui lòng cài đặt sudo hoặc chạy với quyền quản trị."
    fi
    if ! sudo -n true 2>/dev/null; then
        log "Yêu cầu quyền quản trị. Vui lòng nhập mật khẩu sudo."
    fi
}

# Hàm kiểm tra phiên bản Python
check_python_version() {
    if ! command -v python3 &> /dev/null; then
        log "Python3 không được tìm thấy."
        return 1
    fi

    # Kiểm tra xem python3 có phải là Python 3
    if ! python3 -c "import sys; assert sys.version_info.major == 3" 2>/dev/null; then
        log_error "python3 không phải là Python 3. Vui lòng cập nhật hệ thống."
    fi

    # Lấy phiên bản Python
    local version
    version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [ "$version" != "$PYTHON_VERSION" ]; then
        log "Yêu cầu Python $PYTHON_VERSION, nhưng hiện tại là $version."
        return 1
    fi
    log "Python $PYTHON_VERSION đã được cài đặt."
    return 0
}

# Hàm cài đặt Python 3.12
install_python_3_12() {
    log "Kiểm tra và cài đặt Python $PYTHON_VERSION..."
    if check_python_version; then
        return 0
    fi

    local os_type
    os_type=$(uname -s)
    case "$os_type" in
        Linux*)
            check_sudo
            # Kiểm tra bản phân phối Linux
            if [ -f /etc/debian_version ]; then
                # Ubuntu/Debian
                log "Cài đặt Python $PYTHON_VERSION trên Ubuntu/Debian..."
                sudo apt update || log_error "Không thể cập nhật gói."
                sudo apt install -y software-properties-common
                sudo add-apt-repository -y ppa:deadsnakes/ppa || log_error "Không thể thêm PPA."
                sudo apt update
                sudo apt install -y python3.12 python3.12-venv python3.12-dev || log_error "Cài đặt Python thất bại."
                sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
            elif [ -f /etc/redhat-release ]; then
                # CentOS/RHEL
                log "Cài đặt Python $PYTHON_VERSION trên CentOS/RHEL..."
                sudo dnf install -y epel-release
                sudo dnf install -y python3.12 python3.12-devel python3.12-pip || log_error "Cài đặt Python thất bại."
            elif [ -f /etc/fedora-release ]; then
                # Fedora
                log "Cài đặt Python $PYTHON_VERSION trên Fedora..."
                sudo dnf install -y python3.12 python3.12-devel python3.12-pip || log_error "Cài đặt Python thất bại."
            else
                log_error "Bản phân phối Linux không được hỗ trợ tự động. Vui lòng cài đặt Python $PYTHON_VERSION thủ công."
            fi
            ;;
        Darwin*)
            # macOS
            log "Cài đặt Python $PYTHON_VERSION trên macOS..."
            if ! command -v brew &> /dev/null; then
                log "Homebrew không được cài đặt. Bạn có muốn cài đặt Homebrew? (y/n)"
                read -r response
                if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
                    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || log_error "Cài đặt Homebrew thất bại."
                else
                    log_error "Homebrew là bắt buộc để cài đặt Python trên macOS."
                fi
            fi
            brew install python@3.12 || log_error "Cài đặt Python thất bại."
            brew link python@3.12 || log "Cảnh báo: Không thể liên kết python@3.12. Có thể cần chạy 'brew link --overwrite python@3.12'."
            ;;
        *)
            log_error "Hệ điều hành không được hỗ trợ: $os_type"
            ;;
    esac

    # Kiểm tra lại sau khi cài đặt
    if ! check_python_version; then
        log_error "Cài đặt Python $PYTHON_VERSION thất bại."
    fi
}

# Hàm tạo và kích hoạt môi trường ảo
setup_virtualenv() {
    log "Kiểm tra môi trường ảo tại $VENV_DIR..."
    if [ -d "$VENV_DIR" ]; then
        if [ ! -f "$VENV_DIR/bin/activate" ]; then
            log "Môi trường ảo bị hỏng. Xóa và tạo lại..."
            rm -rf "$VENV_DIR"
        else
            log "Môi trường ảo đã tồn tại."
        fi
    fi

    if [ ! -d "$VENV_DIR" ]; then
        log "Tạo môi trường ảo..."
        python3 -m venv "$VENV_DIR" || log_error "Tạo môi trường ảo thất bại."
    fi

    log "Kích hoạt môi trường ảo..."
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate" || log_error "Kích hoạt môi trường ảo thất bại."
}

# Hàm kiểm tra CUDA cho PyTorch
check_cuda() {
    if command -v nvidia-smi &> /dev/null; then
        log "Phát hiện GPU NVIDIA. Sử dụng PyTorch với CUDA."
        echo "https://download.pytorch.org/whl/cu128"
    else
        log "Không phát hiện GPU NVIDIA. Sử dụng PyTorch CPU."
        echo ""
    fi
}

# Hàm tạo requirements.txt
create_requirements() {
    log "Tạo tệp $REQUIREMENTS_FILE..."
    cat > "$REQUIREMENTS_FILE" << EOF
websocket-client
EOF
}

# Hàm cài đặt thư viện
install_libraries() {
    log "Nâng cấp pip..."
    python3 -m pip install --upgrade pip || log_error "Nâng cấp pip thất bại."

    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        create_requirements
    fi

    log "Cài đặt thư viện từ $REQUIREMENTS_FILE..."
    pip install -r "$REQUIREMENTS_FILE" || log_error "Cài đặt thư viện thất bại."

    if [ -f "$COMFYUI_REQUIREMENTS" ]; then
        log "Cài đặt PyTorch..."
        local cuda_url
        cuda_url=$(check_cuda)
        if [ -n "$cuda_url" ]; then
            pip install torch torchvision torchaudio --index-url "$cuda_url" || log_error "Cài đặt PyTorch thất bại."
        fi
        log "Cài đặt thư viện từ $COMFYUI_REQUIREMENTS..."
        pip install -r "$COMFYUI_REQUIREMENTS" || log_error "Cài đặt từ $COMFYUI_REQUIREMENTS thất bại."
    else
        log_error "Không tìm thấy tệp $COMFYUI_REQUIREMENTS."
    fi
}

# Hàm chính
main() {
    log "Bắt đầu cài đặt môi trường..."
    install_python_3_12
    setup_virtualenv
    install_libraries
    log "Hoàn tất cài đặt môi trường!"
}

# Xử lý lỗi
trap 'log_error "Lỗi xảy ra tại dòng $LINENO. Thoát..."' ERR

# Chạy hàm chính
main
