#!/bin/bash
# Script khởi động AI Chat cho Raspberry Pi
# Tự động chạy khi boot

# Đợi X server khởi động (nếu cần)
sleep 3

# Lấy đường dẫn thư mục dự án
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Chuyển đến thư mục dự án
cd "$PROJECT_DIR" || exit 1

# Thiết lập biến môi trường
export DISPLAY=:0
export XAUTHORITY=/home/pi/.Xauthority

# Thiết lập Python path
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Kích hoạt virtual environment nếu có
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Kiểm tra kết nối internet
echo "🔍 Đang kiểm tra kết nối internet..."
INTERNET_STATUS=$(bash "$SCRIPT_DIR/check_internet.sh" 2>/dev/null || echo "NO_INTERNET")

if [ "$INTERNET_STATUS" != "OK" ]; then
    echo "⚠️  Chưa có kết nối internet"
    echo "📡 Đang setup WiFi hotspot..."
    
    # Setup WiFi hotspot
    sudo bash "$SCRIPT_DIR/setup_wifi_hotspot.sh" 2>&1 | tee -a "$PROJECT_DIR/logs/hotspot.log"
    
    # Đợi hotspot khởi động
    sleep 5
    
    # Chạy web server để cấu hình WiFi
    echo "🌐 Đang khởi động web server cấu hình WiFi..."
    echo "   Kết nối WiFi: AIChat-Setup / aichat12345"
    echo "   Truy cập: http://192.168.4.1"
    
    # Chạy web server (chạy trong background, nhưng log ra file)
    python3 "$SCRIPT_DIR/wifi_config_server.py" >> "$PROJECT_DIR/logs/wifi_config.log" 2>&1 &
    WIFI_SERVER_PID=$!
    
    # Đợi người dùng cấu hình WiFi (hoặc timeout sau 30 phút)
    TIMEOUT=1800  # 30 phút
    ELAPSED=0
    
    while [ $ELAPSED -lt $TIMEOUT ]; do
        sleep 5
        ELAPSED=$((ELAPSED + 5))
        
        # Kiểm tra lại internet
        INTERNET_STATUS=$(bash "$SCRIPT_DIR/check_internet.sh" 2>/dev/null || echo "NO_INTERNET")
        
        if [ "$INTERNET_STATUS" == "OK" ]; then
            echo "✅ Đã kết nối internet thành công!"
            
            # Dừng web server
            kill $WIFI_SERVER_PID 2>/dev/null || true
            
            # Dừng hotspot
            sudo systemctl stop hostapd 2>/dev/null || true
            sudo systemctl stop dnsmasq 2>/dev/null || true
            
            # Đợi một chút để network ổn định
            sleep 3
            break
        fi
        
        # Hiển thị thông báo mỗi 30 giây
        if [ $((ELAPSED % 30)) -eq 0 ]; then
            echo "⏳ Đang chờ cấu hình WiFi... ($(($ELAPSED / 60)) phút / $(($TIMEOUT / 60)) phút)"
        fi
    done
    
    # Nếu timeout mà vẫn chưa có internet
    if [ "$INTERNET_STATUS" != "OK" ]; then
        echo "⏰ Timeout! Vẫn chưa có internet"
        echo "   Ứng dụng sẽ không khởi động"
        exit 1
    fi
fi

echo "✅ Đã có kết nối internet, đang khởi động ứng dụng..."

# Chạy ứng dụng với GUI mode
python3 main.py --mode gui --protocol websocket 2>&1 | tee -a "$PROJECT_DIR/logs/startup.log"

