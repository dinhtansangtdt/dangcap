# Quick Start - Tự động boot vào GUI

## 🚀 Cài đặt nhanh (3 bước)

### Bước 1: Kích hoạt thiết bị (chỉ cần làm 1 lần)

```bash
cd ~/dangcap/aichat
python3 main.py --mode gui
# Hoàn tất quy trình kích hoạt, sau đó đóng ứng dụng
```

### Bước 2: Setup autostart

```bash
cd ~/dangcap/aichat
chmod +x scripts/setup_boot_gui.sh
./scripts/setup_boot_gui.sh
```

**Chọn:**
- Option 1: Desktop Autostart (đơn giản, cần desktop)
- Option 2: Systemd Service (khuyến nghị, chạy sớm hơn)

### Bước 3: Reboot và test

```bash
sudo reboot
```

Sau khi reboot, ứng dụng sẽ tự động khởi động! ✅

---

## 📋 Nếu dùng Desktop Autostart

Cần bật auto-login:

```bash
sudo raspi-config
# System Options → Boot / Auto Login → Desktop Autologin
```

---

## 🔍 Kiểm tra

```bash
# Xem log
tail -f ~/dangcap/aichat/logs/gui.log

# Nếu dùng systemd
sudo systemctl status aichat-gui.service
```

---

## 🛑 Tắt autostart

```bash
./scripts/disable_boot_gui.sh
```

---

Xem hướng dẫn chi tiết: `HUONG_DAN_CAI_DAT_BOOT_GUI.md`
