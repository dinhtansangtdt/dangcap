#!/bin/bash
# Script thiết lập tự động boot vào GUI trên Raspberry Pi
# Hỗ trợ cả autostart (desktop) và systemd service

set -e

# Lấy thông tin user và đường dẫn
CURRENT_USER=$(whoami)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
AUTOSTART_DIR="$HOME/.config/autostart"
SERVICE_TEMPLATE="$SCRIPT_DIR/aichat-gui.service.template"
SERVICE_FILE="/etc/systemd/system/aichat-gui.service"

echo "🚀 Thiết lập tự động boot vào GUI..."
echo "   User: $CURRENT_USER"
echo "   Project: $PROJECT_DIR"
echo ""

# Đảm bảo script run_gui_desktop.sh có quyền thực thi
chmod +x "$PROJECT_DIR/scripts/run_gui_desktop.sh"

# Kiểm tra quyền sudo
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "📋 Chọn phương pháp:"
    echo "   1. Autostart (không cần sudo) - Chạy sau khi desktop sẵn sàng"
    echo "   2. Systemd service (cần sudo) - Chạy sớm hơn, không cần desktop"
    echo ""
    read -p "Chọn (1 hoặc 2, mặc định 1): " choice
    choice=${choice:-1}
else
    echo "📋 Chọn phương pháp:"
    echo "   1. Autostart (desktop environment)"
    echo "   2. Systemd service (khuyến nghị - chạy sớm hơn)"
    echo ""
    read -p "Chọn (1 hoặc 2, mặc định 2): " choice
    choice=${choice:-2}
fi

if [ "$choice" = "1" ]; then
    # Phương pháp 1: Autostart (đơn giản, không cần sudo)
    echo ""
    echo "📝 Đang thiết lập Autostart..."
    
    # Tạo thư mục autostart nếu chưa có
    mkdir -p "$AUTOSTART_DIR"
    
    # Tạo desktop file cho autostart
    AUTOSTART_FILE="$AUTOSTART_DIR/aichat-gui.desktop"
    cat > "$AUTOSTART_FILE" << EOF
[Desktop Entry]
Type=Application
Name=AI Chat GUI
Comment=Trợ lý AI thông minh - Tự động khởi động
Exec=$PROJECT_DIR/scripts/run_gui_desktop.sh
Path=$PROJECT_DIR
Icon=$PROJECT_DIR/assets/icon.png
Terminal=false
Categories=Utility;Network;
StartupNotify=true
X-GNOME-Autostart-enabled=true
EOF
    
    # Set executable permissions
    chmod +x "$AUTOSTART_FILE"
    
    echo "✅ Đã tạo autostart file: $AUTOSTART_FILE"
    echo ""
    echo "📋 Các bước tiếp theo:"
    echo "   1. Đảm bảo đã bật auto-login vào desktop:"
    echo "      sudo raspi-config"
    echo "      → System Options → Boot / Auto Login → Desktop Autologin"
    echo ""
    echo "   2. Reboot để test:"
    echo "      sudo reboot"
    echo ""
    echo "   3. Kiểm tra log:"
    echo "      tail -f $PROJECT_DIR/logs/gui.log"
    echo ""
    echo "🛑 Để tắt autostart:"
    echo "   rm $AUTOSTART_FILE"
    
else
    # Phương pháp 2: Systemd service (chạy sớm hơn)
    echo ""
    echo "📝 Đang thiết lập Systemd Service..."
    
    if [ ! -f "$SERVICE_TEMPLATE" ]; then
        echo "❌ Không tìm thấy file template: $SERVICE_TEMPLATE"
        exit 1
    fi
    
    # Tạo service file với user và path đúng
    TEMP_SERVICE="/tmp/aichat-gui.service"
    sed "s|__USER__|$CURRENT_USER|g; s|__PROJECT_DIR__|$PROJECT_DIR|g; s|__HOME__|$HOME|g" "$SERVICE_TEMPLATE" > "$TEMP_SERVICE"
    
    # Copy service file vào systemd
    sudo cp "$TEMP_SERVICE" "$SERVICE_FILE"
    rm "$TEMP_SERVICE"
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable service
    sudo systemctl enable aichat-gui.service
    
    echo "✅ Đã cài đặt systemd service"
    echo ""
    echo "📋 Các bước tiếp theo:"
    echo "   1. Khởi động service ngay (tùy chọn):"
    echo "      sudo systemctl start aichat-gui.service"
    echo ""
    echo "   2. Kiểm tra trạng thái:"
    echo "      sudo systemctl status aichat-gui.service"
    echo ""
    echo "   3. Xem log:"
    echo "      sudo journalctl -u aichat-gui.service -f"
    echo ""
    echo "   4. Reboot để test:"
    echo "      sudo reboot"
    echo ""
    echo "🛑 Để tắt service:"
    echo "   sudo systemctl disable aichat-gui.service"
    echo "   sudo systemctl stop aichat-gui.service"
fi

echo ""
echo "✨ Hoàn tất!"
echo ""
echo "💡 Lưu ý:"
echo "   - Đảm bảo đã kích hoạt thiết bị trước: python3 main.py --mode gui"
echo "   - Nếu dùng virtual environment, script sẽ tự động kích hoạt"
echo "   - Log sẽ được lưu trong: $PROJECT_DIR/logs/gui.log"
echo "   - Systemd service sẽ tự động restart nếu ứng dụng bị lỗi"
