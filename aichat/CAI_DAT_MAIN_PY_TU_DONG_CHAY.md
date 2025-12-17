# Hướng dẫn: Raspberry Pi khởi động thì main.py chạy luôn

## 🎯 Mục tiêu
Khi Raspberry Pi boot lên → `main.py` tự động chạy ngay

---

## 📝 Các bước thực hiện

### Bước 1: Vào thư mục dự án

```bash
cd ~/dangcap/aichat
# Hoặc đường dẫn thực tế của bạn
```

### Bước 2: Chạy script setup

```bash
chmod +x scripts/setup_boot_gui.sh
./scripts/setup_boot_gui.sh
```

### Bước 3: Chọn phương pháp

Khi script hỏi, chọn:

**Option 2 (Systemd Service)** - Khuyến nghị ✅
- Chạy sớm hơn
- Không cần desktop
- Tự động restart nếu lỗi

### Bước 4: Reboot để test

```bash
sudo reboot
```

---

## ✅ Kiểm tra main.py đã chạy

Sau khi reboot, kiểm tra:

```bash
# Kiểm tra process đang chạy
ps aux | grep "main.py"

# Xem log
tail -f ~/dangcap/aichat/logs/gui.log

# Nếu dùng systemd
sudo systemctl status aichat-gui.service
```

---

## 🔄 Quy trình hoạt động

```
Raspberry Pi Boot
    ↓
Systemd khởi động
    ↓
aichat-gui.service chạy
    ↓
run_gui_desktop.sh được gọi
    ↓
Đợi X server sẵn sàng
    ↓
Chạy: python3 main.py --mode gui
    ↓
✅ Ứng dụng GUI hiển thị
```

---

## 🛠️ Xử lý nếu không chạy

### Kiểm tra service

```bash
# Xem trạng thái
sudo systemctl status aichat-gui.service

# Xem log chi tiết
sudo journalctl -u aichat-gui.service -n 50

# Restart service
sudo systemctl restart aichat-gui.service
```

### Kiểm tra script

```bash
# Test chạy thủ công
cd ~/dangcap/aichat
./scripts/run_gui_desktop.sh

# Nếu lỗi, xem log
tail -f logs/gui.log
```

### Kiểm tra main.py

```bash
# Test chạy trực tiếp
cd ~/dangcap/aichat
python3 main.py --mode gui
```

---

## 📋 Checklist

- [ ] Đã chạy `./scripts/setup_boot_gui.sh`
- [ ] Đã chọn option 2 (Systemd Service)
- [ ] Đã reboot
- [ ] Kiểm tra `ps aux | grep main.py` thấy process đang chạy
- [ ] Ứng dụng GUI đã hiển thị

---

## 🎉 Hoàn tất!

Sau khi setup xong, mỗi lần Raspberry Pi boot lên, `main.py` sẽ tự động chạy!
