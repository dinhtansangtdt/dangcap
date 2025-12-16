#!/bin/bash
# Script tắt tự động khởi động GUI

AUTOSTART_FILE="$HOME/.config/autostart/aichat-gui.desktop"

if [ -f "$AUTOSTART_FILE" ]; then
    rm "$AUTOSTART_FILE"
    echo "✅ Đã tắt autostart GUI"
    echo "   File đã xóa: $AUTOSTART_FILE"
else
    echo "⚠️  Không tìm thấy file autostart"
    echo "   File: $AUTOSTART_FILE"
fi
