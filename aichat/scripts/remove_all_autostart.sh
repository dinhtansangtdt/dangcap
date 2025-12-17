#!/bin/bash
# Script xóa hết tất cả service và autostart đã cài

echo "🗑️  Đang xóa tất cả autostart và service..."

# 1. Xóa systemd service
SERVICE_FILE="/etc/systemd/system/aichat-gui.service"
if [ -f "$SERVICE_FILE" ]; then
    echo "📝 Đang xóa systemd service..."
    
    # Disable service
    if sudo systemctl is-enabled aichat-gui.service &>/dev/null; then
        sudo systemctl disable aichat-gui.service
        echo "   ✅ Đã disable service"
    fi
    
    # Stop service
    if sudo systemctl is-active aichat-gui.service &>/dev/null; then
        sudo systemctl stop aichat-gui.service
        echo "   ✅ Đã stop service"
    fi
    
    # Xóa service file
    sudo rm -f "$SERVICE_FILE"
    echo "   ✅ Đã xóa service file: $SERVICE_FILE"
    
    # Reload systemd
    sudo systemctl daemon-reload
    echo "   ✅ Đã reload systemd"
else
    echo "   ℹ️  Không tìm thấy systemd service file"
fi

# 2. Xóa desktop autostart
AUTOSTART_FILE="$HOME/.config/autostart/aichat-gui.desktop"
if [ -f "$AUTOSTART_FILE" ]; then
    rm -f "$AUTOSTART_FILE"
    echo "✅ Đã xóa autostart file: $AUTOSTART_FILE"
else
    echo "ℹ️  Không tìm thấy autostart file"
fi

# 3. Xóa các service file cũ (nếu có)
OLD_SERVICE_FILES=(
    "/etc/systemd/system/aichat.service"
)

for old_file in "${OLD_SERVICE_FILES[@]}"; do
    if [ -f "$old_file" ]; then
        echo "📝 Đang xóa service file cũ: $old_file"
        SERVICE_NAME=$(basename "$old_file" .service)
        
        # Disable và stop
        if sudo systemctl is-enabled "$SERVICE_NAME.service" &>/dev/null; then
            sudo systemctl disable "$SERVICE_NAME.service"
            sudo systemctl stop "$SERVICE_NAME.service"
        fi
        
        # Xóa file
        sudo rm -f "$old_file"
        echo "   ✅ Đã xóa: $old_file"
    fi
done

# 4. Reload systemd một lần nữa
sudo systemctl daemon-reload

# 5. Kiểm tra process đang chạy
echo ""
echo "🔍 Kiểm tra process đang chạy..."
if pgrep -f "main.py --mode gui" > /dev/null; then
    echo "   ⚠️  Có process main.py đang chạy"
    echo "   Để kill: pkill -f 'main.py --mode gui'"
else
    echo "   ✅ Không có process đang chạy"
fi

echo ""
echo "✨ Hoàn tất! Tất cả service và autostart đã được xóa."
echo ""
echo "📋 Để setup lại:"
echo "   ./scripts/setup_boot_gui.sh"
