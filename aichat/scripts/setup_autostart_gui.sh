#!/bin/bash
# Script setup tự động chạy GUI khi boot Raspberry Pi (Autostart method)

# Lấy thông tin user và đường dẫn
CURRENT_USER=$(whoami)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
AUTOSTART_DIR="$HOME/.config/autostart"

echo "🔧 Đang thiết lập tự động khởi động GUI (Autostart)..."
echo "   User: $CURRENT_USER"
echo "   Project: $PROJECT_DIR"
echo ""

# Đảm bảo script có quyền thực thi
chmod +x "$PROJECT_DIR/scripts/run_gui_desktop.sh"

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
echo ""
echo "💡 Lưu ý: Nếu muốn chạy sớm hơn (không cần desktop), dùng:"
echo "   ./scripts/setup_boot_gui.sh (chọn option 2 - Systemd service)"
echo ""
echo "✨ Hoàn tất!"
