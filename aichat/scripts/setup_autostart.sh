#!/bin/bash
# Script tự động setup autostart cho Raspberry Pi

set -e

echo "=========================================="
echo "  Setup Auto-start cho AI Chat"
echo "=========================================="
echo ""

# Lấy đường dẫn thư mục dự án
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Thư mục dự án: $PROJECT_DIR"
echo ""

# Kiểm tra quyền root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Cần quyền sudo để setup systemd service"
    echo "   Chạy: sudo bash $0"
    exit 1
fi

# Cấp quyền thực thi cho script khởi động
chmod +x "$PROJECT_DIR/scripts/start_aichat.sh"
echo "✅ Đã cấp quyền thực thi cho start_aichat.sh"

# Tạo thư mục log nếu chưa có
mkdir -p "$PROJECT_DIR/logs"
echo "✅ Đã tạo thư mục logs"

# Lấy user hiện tại (user đang chạy script, không phải root)
CURRENT_USER="${SUDO_USER:-$USER}"
if [ "$CURRENT_USER" = "root" ]; then
    # Nếu chạy trực tiếp bằng root, lấy user từ HOME
    CURRENT_USER=$(basename "$HOME")
fi

# Lấy group của user
CURRENT_GROUP=$(id -gn "$CURRENT_USER")

echo "User: $CURRENT_USER"
echo "Group: $CURRENT_GROUP"
echo ""

# Chỉnh sửa đường dẫn và user trong service file
SERVICE_FILE="$PROJECT_DIR/scripts/aichat.service"
TEMP_SERVICE="/tmp/aichat.service.tmp"

# Thay thế đường dẫn và user trong service file
sed -e "s|/home/pi/aichat|$PROJECT_DIR|g" \
    -e "s|User=pi|User=$CURRENT_USER|g" \
    -e "s|Group=pi|Group=$CURRENT_GROUP|g" \
    -e "s|/home/pi/.Xauthority|/home/$CURRENT_USER/.Xauthority|g" \
    "$SERVICE_FILE" > "$TEMP_SERVICE"

# Copy service file vào systemd
cp "$TEMP_SERVICE" /etc/systemd/system/aichat.service
echo "✅ Đã copy service file vào /etc/systemd/system/"

# Reload systemd
systemctl daemon-reload
echo "✅ Đã reload systemd daemon"

# Hỏi người dùng có muốn enable không
echo ""
read -p "Bạn có muốn kích hoạt tự động khởi động khi boot? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl enable aichat.service
    echo "✅ Đã kích hoạt tự động khởi động"
    
    read -p "Bạn có muốn khởi động service ngay bây giờ? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        systemctl start aichat.service
        echo "✅ Đã khởi động service"
        echo ""
        echo "Kiểm tra trạng thái:"
        systemctl status aichat.service --no-pager
    fi
else
    echo "ℹ️  Service đã được cài đặt nhưng chưa kích hoạt"
    echo "   Để kích hoạt sau: sudo systemctl enable aichat.service"
fi

echo ""
echo "=========================================="
echo "  Setup hoàn tất!"
echo "=========================================="
echo ""
echo "Các lệnh hữu ích:"
echo "  - Xem trạng thái: sudo systemctl status aichat.service"
echo "  - Xem log:        sudo journalctl -u aichat.service -f"
echo "  - Khởi động:      sudo systemctl start aichat.service"
echo "  - Dừng:          sudo systemctl stop aichat.service"
echo "  - Khởi động lại: sudo systemctl restart aichat.service"
echo "  - Tắt auto-start: sudo systemctl disable aichat.service"
echo ""

