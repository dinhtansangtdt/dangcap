#!/bin/bash
# Script setup WiFi hotspot cho Raspberry Pi

set -e

echo "=========================================="
echo "  Setup WiFi Hotspot"
echo "=========================================="

# Cấu hình hotspot
SSID="AIChat-Setup"
PASSWORD="aichat12345"
INTERFACE="wlan0"
IP="192.168.4.1"

# Kiểm tra quyền root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Cần quyền sudo"
    exit 1
fi

# Kiểm tra hostapd và dnsmasq đã cài chưa
if ! command -v hostapd &> /dev/null; then
    echo "📦 Đang cài đặt hostapd..."
    apt-get update
    apt-get install -y hostapd dnsmasq
fi

# Tắt các service
systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true

# Backup config cũ
cp /etc/dhcpcd.conf /etc/dhcpcd.conf.backup 2>/dev/null || true
cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup 2>/dev/null || true

# Cấu hình dhcpcd
if ! grep -q "interface $INTERFACE" /etc/dhcpcd.conf; then
    cat >> /etc/dhcpcd.conf << EOF

# WiFi Hotspot configuration
interface $INTERFACE
static ip_address=$IP/24
nohook wpa_supplicant
EOF
fi

# Cấu hình dnsmasq
cat > /etc/dnsmasq.conf << EOF
interface=$INTERFACE
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=local
address=/#/$IP
EOF

# Cấu hình hostapd
cat > /etc/hostapd/hostapd.conf << EOF
interface=$INTERFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Cấu hình hostapd daemon
sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

# Khởi động lại network
systemctl restart dhcpcd
sleep 2

# Khởi động dnsmasq và hostapd
systemctl unmask hostapd
systemctl enable hostapd
systemctl enable dnsmasq
systemctl start hostapd
systemctl start dnsmasq

echo "✅ WiFi Hotspot đã được setup!"
echo "   SSID: $SSID"
echo "   Password: $PASSWORD"
echo "   IP: $IP"

