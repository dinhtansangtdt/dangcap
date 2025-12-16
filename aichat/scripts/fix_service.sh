#!/bin/bash
# Script sửa service file với user và đường dẫn đúng

set -e

if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Cần quyền sudo"
    echo "   Chạy: sudo bash $0"
    exit 1
fi

# Lấy user hiện tại
CURRENT_USER="${SUDO_USER:-$USER}"
if [ "$CURRENT_USER" = "root" ]; then
    CURRENT_USER=$(basename "$HOME")
fi

CURRENT_GROUP=$(id -gn "$CURRENT_USER")

# Lấy đường dẫn dự án từ service file hiện tại
CURRENT_SERVICE="/etc/systemd/system/aichat.service"
if [ ! -f "$CURRENT_SERVICE" ]; then
    echo "❌ Service file không tồn tại: $CURRENT_SERVICE"
    exit 1
fi

# Lấy đường dẫn từ ExecStart
EXEC_START=$(grep "^ExecStart=" "$CURRENT_SERVICE" | cut -d'=' -f2- | sed 's|/scripts/start_aichat.sh||')
if [ -z "$EXEC_START" ]; then
    echo "⚠️  Không tìm thấy đường dẫn trong service file"
    echo "   Vui lòng chỉ định đường dẫn dự án:"
    read -p "Đường dẫn dự án: " PROJECT_DIR
else
    PROJECT_DIR="$EXEC_START"
fi

echo "=========================================="
echo "  Sửa Service File"
echo "=========================================="
echo "User: $CURRENT_USER"
echo "Group: $CURRENT_GROUP"
echo "Đường dẫn: $PROJECT_DIR"
echo ""

# Backup service file cũ
cp "$CURRENT_SERVICE" "${CURRENT_SERVICE}.backup"
echo "✅ Đã backup service file cũ"

# Sửa service file
sed -i \
    -e "s|^User=.*|User=$CURRENT_USER|g" \
    -e "s|^Group=.*|Group=$CURRENT_GROUP|g" \
    -e "s|^WorkingDirectory=.*|WorkingDirectory=$PROJECT_DIR|g" \
    -e "s|^ExecStart=.*|ExecStart=$PROJECT_DIR/scripts/start_aichat.sh|g" \
    -e "s|/home/[^/]*/.Xauthority|/home/$CURRENT_USER/.Xauthority|g" \
    "$CURRENT_SERVICE"

echo "✅ Đã sửa service file"

# Reload systemd
systemctl daemon-reload
echo "✅ Đã reload systemd"

# Kiểm tra service
echo ""
echo "Kiểm tra service file:"
cat "$CURRENT_SERVICE"
echo ""

# Hỏi có muốn restart không
read -p "Bạn có muốn khởi động lại service? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl restart aichat.service
    echo "✅ Đã khởi động lại service"
    sleep 2
    systemctl status aichat.service --no-pager
fi

echo ""
echo "✅ Hoàn tất!"

