#!/bin/bash
# Script kiểm tra kết nối internet

# Số lần thử ping
PING_COUNT=3
TIMEOUT=5

# Danh sách server để ping
SERVERS=("8.8.8.8" "1.1.1.1" "google.com")

check_internet() {
    for server in "${SERVERS[@]}"; do
        if ping -c $PING_COUNT -W $TIMEOUT "$server" > /dev/null 2>&1; then
            return 0  # Có internet
        fi
    done
    return 1  # Không có internet
}

# Kiểm tra kết nối
if check_internet; then
    echo "OK"
    exit 0
else
    echo "NO_INTERNET"
    exit 1
fi

