#!/bin/bash
# Script chạy GUI với desktop launcher (ẩn terminal)
# Chỉ đợi X server, không đợi network

# Lấy đường dẫn dự án
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR" || exit 1

# Tạo thư mục logs nếu chưa có
mkdir -p "$PROJECT_DIR/logs"
LOG_FILE="$PROJECT_DIR/logs/gui.log"

# Function để log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "Bắt đầu khởi động GUI..."

# Thiết lập biến môi trường X
export DISPLAY=:0
export XAUTHORITY="$HOME/.Xauthority"

# Đợi X server sẵn sàng (tối đa 90 giây)
log "Đang đợi X server sẵn sàng..."
X_READY=false
for i in {1..90}; do
    if xset q &>/dev/null 2>&1; then
        X_READY=true
        log "X server đã sẵn sàng"
        break
    fi
    sleep 1
done

if [ "$X_READY" = false ]; then
    log "Lỗi: X server không sẵn sàng sau 90 giây"
    exit 1
fi

# Đợi thêm một chút để đảm bảo X server ổn định
log "Đợi 2 giây để đảm bảo X server ổn định..."
sleep 2

# Kích hoạt venv nếu có
if [ -d "venv" ]; then
    source venv/bin/activate
    log "Đã kích hoạt venv: venv"
    PYTHON_CMD="python3"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    log "Đã kích hoạt venv: .venv"
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python3"
    log "Không tìm thấy venv, dùng system python3"
fi

# Kiểm tra main.py có tồn tại không
if [ ! -f "main.py" ]; then
    log "Lỗi: Không tìm thấy file main.py trong $PROJECT_DIR"
    exit 1
fi

# Kiểm tra python3 có sẵn không
if ! command -v "$PYTHON_CMD" &> /dev/null; then
    log "Lỗi: Không tìm thấy $PYTHON_CMD"
    exit 1
fi

# Chạy GUI với đường dẫn đầy đủ (redirect log)
log "Khởi động ứng dụng GUI (không đợi network)..."
log "Working directory: $PROJECT_DIR"
log "Python command: $PYTHON_CMD"
log "Main file: $PROJECT_DIR/main.py"

# Chạy main.py với đường dẫn đầy đủ
# Đảm bảo chạy từ đúng thư mục để import modules đúng
cd "$PROJECT_DIR"
exec "$PYTHON_CMD" main.py --mode gui >> "$LOG_FILE" 2>&1
