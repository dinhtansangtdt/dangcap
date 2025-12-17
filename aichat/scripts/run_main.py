#!/bin/bash
# Script đơn giản để chạy main.py trực tiếp

# Lấy đường dẫn dự án
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR" || exit 1

# Kích hoạt venv nếu có
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Chạy main.py
python3 "$PROJECT_DIR/main.py" "$@"
