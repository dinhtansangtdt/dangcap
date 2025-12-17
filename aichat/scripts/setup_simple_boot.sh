#!/bin/bash
# Script setup đơn giản: chạy cd và python3 main.py khi boot

set -e

# Lấy thông tin user và đường dẫn
CURRENT_USER=$(whoami)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_TEMPLATE="$SCRIPT_DIR/aichat-simple.service.template"
SERVICE_FILE="/etc/systemd/system/aichat-simple.service"

echo "🚀 Thiết lập tự động boot - chạy: cd ~/dangcap/aichat && python3 main.py"
echo "   User: $CURRENT_USER"
echo "   Project: $PROJECT_DIR"
echo ""

# Đảm bảo script có quyền thực thi
chmod +x "$PROJECT_DIR/scripts/run_simple.sh"

# Kiểm tra quyền sudo
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "❌ Cần quyền sudo để cài đặt systemd service"
    exit 1
fi

# Tạo service file
if [ ! -f "$SERVICE_TEMPLATE" ]; then
    echo "❌ Không tìm thấy file template: $SERVICE_TEMPLATE"
    exit 1
fi

# Tạo service file với user và path đúng
TEMP_SERVICE="/tmp/aichat-simple.service"
sed "s|__USER__|$CURRENT_USER|g; s|__PROJECT_DIR__|$PROJECT_DIR|g; s|__HOME__|$HOME|g" "$SERVICE_TEMPLATE" > "$TEMP_SERVICE"

# Copy service file vào systemd
sudo cp "$TEMP_SERVICE" "$SERVICE_FILE"
rm "$TEMP_SERVICE"

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable aichat-simple.service

echo "✅ Đã cài đặt systemd service"
echo ""
echo "📋 Các bước tiếp theo:"
echo "   1. Khởi động service ngay (tùy chọn):"
echo "      sudo systemctl start aichat-simple.service"
echo ""
echo "   2. Kiểm tra trạng thái:"
echo "      sudo systemctl status aichat-simple.service"
echo ""
echo "   3. Xem log:"
echo "      sudo journalctl -u aichat-simple.service -f"
echo ""
echo "   4. Reboot để test:"
echo "      sudo reboot"
echo ""
echo "🛑 Để tắt service:"
echo "   sudo systemctl disable aichat-simple.service"
echo "   sudo systemctl stop aichat-simple.service"
echo "   sudo rm $SERVICE_FILE"
echo ""
echo "✨ Hoàn tất!"
