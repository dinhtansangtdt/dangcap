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
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    log "Đã kích hoạt venv: .venv"
fi

# Chạy GUI (redirect log)
log "Khởi động ứng dụng GUI (không đợi network)..."
exec python3 main.py --mode gui >> "$LOG_FILE" 2>&1
