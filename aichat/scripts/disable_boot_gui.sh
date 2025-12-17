#!/bin/bash
# Script tắt tự động khởi động GUI (cả autostart và systemd service)

AUTOSTART_FILE="$HOME/.config/autostart/aichat-gui.desktop"
SERVICE_FILE="/etc/systemd/system/aichat-gui.service"

echo "🛑 Đang tắt tự động khởi động GUI..."
echo ""

# Tắt autostart nếu có
if [ -f "$AUTOSTART_FILE" ]; then
    rm "$AUTOSTART_FILE"
    echo "✅ Đã xóa autostart file: $AUTOSTART_FILE"
else
    echo "ℹ️  Không tìm thấy autostart file"
fi

# Tắt systemd service nếu có
if [ -f "$SERVICE_FILE" ]; then
    if sudo systemctl is-enabled aichat-gui.service &>/dev/null; then
        sudo systemctl stop aichat-gui.service
        sudo systemctl disable aichat-gui.service
        echo "✅ Đã tắt systemd service: aichat-gui.service"
    else
        echo "ℹ️  Systemd service chưa được enable"
    fi
    # Không xóa file, chỉ disable
else
    echo "ℹ️  Không tìm thấy systemd service file"
fi

echo ""
echo "✨ Hoàn tất!"
echo ""
echo "💡 Để xóa hết (bao gồm file service):"
echo "   ./scripts/remove_all_autostart.sh"
