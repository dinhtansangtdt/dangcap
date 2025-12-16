#!/bin/bash
# Script cấu hình WiFi từ SSID và password

set -e

if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Cần quyền sudo"
    exit 1
fi

SSID="$1"
PASSWORD="$2"

if [ -z "$SSID" ]; then
    echo "❌ SSID không được để trống"
    exit 1
fi

echo "=========================================="
echo "  Cấu hình WiFi"
echo "=========================================="
echo "SSID: $SSID"
echo ""

# Dừng hotspot
systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true

# Khôi phục dhcpcd.conf
if [ -f /etc/dhcpcd.conf.backup ]; then
    cp /etc/dhcpcd.conf.backup /etc/dhcpcd.conf
fi

# Xóa dòng hotspot trong dhcpcd.conf
sed -i '/interface wlan0/,/nohook wpa_supplicant/d' /etc/dhcpcd.conf

# Tạo wpa_supplicant config
WPA_CONFIG="/etc/wpa_supplicant/wpa_supplicant.conf"

# Backup config cũ
if [ -f "$WPA_CONFIG" ]; then
    cp "$WPA_CONFIG" "${WPA_CONFIG}.backup"
fi

# Thêm network mới
if [ -z "$PASSWORD" ]; then
    # WiFi không có password
    NETWORK_CONFIG="network={\n    ssid=\"$SSID\"\n    key_mgmt=NONE\n}"
else
    # WiFi có password
    NETWORK_CONFIG="network={\n    ssid=\"$SSID\"\n    psk=\"$PASSWORD\"\n}"
fi

# Kiểm tra xem network đã tồn tại chưa
if ! grep -q "ssid=\"$SSID\"" "$WPA_CONFIG" 2>/dev/null; then
    echo -e "$NETWORK_CONFIG" >> "$WPA_CONFIG"
fi

# Khởi động lại network
systemctl restart dhcpcd
sleep 3

# Khởi động lại wpa_supplicant
wpa_cli -i wlan0 reconfigure 2>/dev/null || true

echo "✅ Đã cấu hình WiFi"
echo "   Đang khởi động lại sau 5 giây..."
sleep 5

# Reboot
reboot

