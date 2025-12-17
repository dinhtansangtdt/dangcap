# Hướng dẫn cài đặt tự động boot vào GUI trên Raspberry Pi

## 📋 Mục lục
1. [Chuẩn bị](#chuẩn-bị)
2. [Cài đặt Dependencies](#cài-đặt-dependencies)
3. [Kích hoạt thiết bị](#kích-hoạt-thiết-bị)
4. [Thiết lập Auto Boot](#thiết-lập-auto-boot)
5. [Kiểm tra và xử lý lỗi](#kiểm-tra-và-xử-lý-lỗi)

---

## 1. Chuẩn bị

### Bước 1.1: Kết nối vào Raspberry Pi

```bash
# Nếu dùng SSH
ssh pi@raspberrypi.local
# Hoặc
ssh pi@<IP_ADDRESS>

# Nếu dùng trực tiếp trên RPi, mở Terminal
```

### Bước 1.2: Di chuyển đến thư mục dự án

```bash
cd ~/dangcap/aichat
# Hoặc đường dẫn thực tế của bạn
cd /home/pi/dangcap/aichat
```

### Bước 1.3: Kiểm tra các file cần thiết

```bash
# Kiểm tra các script có tồn tại không
ls -la scripts/run_gui_desktop.sh
ls -la scripts/setup_boot_gui.sh
ls -la scripts/aichat-gui.service.template

# Nếu không có, đảm bảo đã clone/pull code mới nhất
git pull
```

---

## 2. Cài đặt Dependencies

### Bước 2.1: Cập nhật hệ thống

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### Bước 2.2: Cài đặt Python dependencies

```bash
# Nếu dùng virtual environment
python3 -m venv venv
source venv/bin/activate

# Cài đặt packages
pip3 install -r requirements.txt

# Nếu có requirements_rpi.txt
pip3 install -r requirements_rpi.txt
```

### Bước 2.3: Cài đặt system dependencies (nếu cần)

```bash
# Các package cơ bản thường đã có sẵn trên Raspberry Pi OS
# Chỉ cài thêm nếu thiếu:
sudo apt-get install -y python3-pip python3-venv
```

---

## 3. Kích hoạt thiết bị

### Bước 3.1: Chạy ứng dụng lần đầu để kích hoạt

```bash
cd ~/dangcap/aichat

# Kích hoạt venv nếu có
source venv/bin/activate  # hoặc source .venv/bin/activate

# Chạy ứng dụng GUI
python3 main.py --mode gui
```

### Bước 3.2: Hoàn tất quy trình kích hoạt

- Làm theo hướng dẫn trên màn hình để kích hoạt thiết bị
- Đảm bảo đã kích hoạt thành công trước khi tiếp tục

### Bước 3.3: Test ứng dụng hoạt động

```bash
# Đóng ứng dụng (nếu đang chạy)
# Chạy lại để test
python3 main.py --mode gui

# Nếu chạy OK, nhấn Ctrl+C để dừng
```

---

## 4. Thiết lập Auto Boot

### Bước 4.1: Cấp quyền thực thi cho scripts

```bash
cd ~/dangcap/aichat

# Cấp quyền cho tất cả scripts
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

### Bước 4.2: Chọn phương pháp autostart

Có 2 phương pháp:

#### **Phương pháp A: Systemd Service (Khuyến nghị)**

**Ưu điểm:**
- ✅ Chạy sớm hơn, không cần desktop
- ✅ Tự động restart nếu lỗi
- ✅ Quản lý dễ dàng qua systemctl

**Nhược điểm:**
- ⚠️ Cần quyền sudo

#### **Phương pháp B: Desktop Autostart**

**Ưu điểm:**
- ✅ Đơn giản, không cần sudo
- ✅ Chạy sau khi desktop sẵn sàng

**Nhược điểm:**
- ⚠️ Cần desktop environment
- ⚠️ Cần bật auto-login

---

### Bước 4.3A: Thiết lập Systemd Service

```bash
cd ~/dangcap/aichat

# Chạy script setup
chmod +x scripts/setup_boot_gui.sh
./scripts/setup_boot_gui.sh
```

**Khi được hỏi, chọn option 2 (Systemd service)**

Script sẽ:
1. Tự động detect user và đường dẫn
2. Tạo systemd service file
3. Enable service để tự động chạy khi boot

**Kiểm tra service đã được tạo:**

```bash
# Kiểm tra service file
sudo systemctl status aichat-gui.service

# Xem log
sudo journalctl -u aichat-gui.service -f
```

**Test khởi động service ngay:**

```bash
# Khởi động service
sudo systemctl start aichat-gui.service

# Kiểm tra trạng thái
sudo systemctl status aichat-gui.service

# Nếu có lỗi, xem log chi tiết
sudo journalctl -u aichat-gui.service -n 50
```

---

### Bước 4.3B: Thiết lập Desktop Autostart

```bash
cd ~/dangcap/aichat

# Chạy script setup
chmod +x scripts/setup_autostart_gui.sh
./scripts/setup_autostart_gui.sh
```

**Bật auto-login vào desktop:**

```bash
# Cách 1: Dùng raspi-config (khuyến nghị)
sudo raspi-config
```

Trong menu:
1. Chọn `System Options`
2. Chọn `Boot / Auto Login`
3. Chọn `Desktop Autologin`
4. Chọn user của bạn (thường là `pi`)
5. Finish và reboot

**Hoặc cách 2: Sửa file trực tiếp**

```bash
sudo nano /etc/lightdm/lightdm.conf
```

Tìm và sửa:
```ini
[Seat:*]
autologin-user=pi  # Thay bằng user của bạn
autologin-user-timeout=0
```

Lưu file (Ctrl+O, Enter, Ctrl+X)

---

## 5. Kiểm tra và xử lý lỗi

### Bước 5.1: Reboot để test

```bash
sudo reboot
```

Sau khi reboot, ứng dụng GUI sẽ tự động khởi động.

### Bước 5.2: Kiểm tra ứng dụng đã chạy

**Nếu dùng Systemd Service:**

```bash
# Kiểm tra trạng thái
sudo systemctl status aichat-gui.service

# Xem log real-time
sudo journalctl -u aichat-gui.service -f

# Xem log ứng dụng
tail -f ~/dangcap/aichat/logs/gui.log
```

**Nếu dùng Desktop Autostart:**

```bash
# Kiểm tra process
ps aux | grep "main.py"

# Xem log
tail -f ~/dangcap/aichat/logs/gui.log
```

### Bước 5.3: Xử lý các lỗi thường gặp

#### **Lỗi 1: Service không chạy**

```bash
# Kiểm tra service
sudo systemctl status aichat-gui.service

# Xem log chi tiết
sudo journalctl -u aichat-gui.service -n 100

# Restart service
sudo systemctl restart aichat-gui.service
```

#### **Lỗi 2: X server không sẵn sàng**

```bash
# Kiểm tra X server
echo $DISPLAY  # Phải hiển thị :0
xset q         # Phải không có lỗi

# Nếu lỗi, đảm bảo đã login vào desktop
```

#### **Lỗi 3: Permission denied**

```bash
# Kiểm tra quyền
ls -la scripts/run_gui_desktop.sh

# Cấp quyền lại
chmod +x scripts/run_gui_desktop.sh
chmod +x scripts/setup_boot_gui.sh

# Kiểm tra quyền sở hữu
sudo chown -R $USER:$USER ~/dangcap/aichat
```

#### **Lỗi 4: Đường dẫn sai**

```bash
# Kiểm tra đường dẫn trong service file
sudo cat /etc/systemd/system/aichat-gui.service

# Nếu sai, sửa lại:
sudo nano /etc/systemd/system/aichat-gui.service
# Sửa WorkingDirectory và ExecStart cho đúng

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl restart aichat-gui.service
```

#### **Lỗi 5: Virtual environment không được kích hoạt**

```bash
# Kiểm tra script run_gui_desktop.sh có kích hoạt venv không
cat scripts/run_gui_desktop.sh | grep venv

# Nếu không có, đảm bảo venv ở đúng vị trí:
# - venv/ hoặc .venv/ trong thư mục dự án
```

### Bước 5.4: Test chạy thủ công

```bash
cd ~/dangcap/aichat

# Kích hoạt venv nếu có
source venv/bin/activate

# Chạy script trực tiếp
./scripts/run_gui_desktop.sh

# Nếu chạy OK, có nghĩa là script đúng
# Nếu lỗi, xem log để debug
tail -f logs/gui.log
```

---

## 6. Quản lý Service

### Dừng service

```bash
sudo systemctl stop aichat-gui.service
```

### Khởi động lại service

```bash
sudo systemctl restart aichat-gui.service
```

### Tắt tự động khởi động

```bash
sudo systemctl disable aichat-gui.service
sudo systemctl stop aichat-gui.service
```

### Bật lại tự động khởi động

```bash
sudo systemctl enable aichat-gui.service
sudo systemctl start aichat-gui.service
```

### Xem log real-time

```bash
# Systemd log
sudo journalctl -u aichat-gui.service -f

# Application log
tail -f ~/dangcap/aichat/logs/gui.log
```

---

## 7. Tắt Autostart (nếu cần)

### Nếu dùng Systemd Service:

```bash
sudo systemctl disable aichat-gui.service
sudo systemctl stop aichat-gui.service
```

### Nếu dùng Desktop Autostart:

```bash
rm ~/.config/autostart/aichat-gui.desktop
```

### Hoặc dùng script:

```bash
./scripts/disable_boot_gui.sh
```

---

## 8. Checklist hoàn tất

- [ ] Đã cài đặt dependencies
- [ ] Đã kích hoạt thiết bị thành công
- [ ] Đã chạy script setup (systemd hoặc autostart)
- [ ] Đã test service/autostart hoạt động
- [ ] Đã reboot và kiểm tra tự động khởi động
- [ ] Ứng dụng GUI tự động hiển thị sau khi boot

---

## 9. Lưu ý quan trọng

1. **Đảm bảo đã kích hoạt thiết bị** trước khi setup autostart
2. **Kiểm tra đường dẫn** trong service file phải đúng với vị trí dự án
3. **Nếu dùng venv**, đảm bảo venv ở đúng vị trí (`venv/` hoặc `.venv/`)
4. **Log files** sẽ được lưu trong `logs/gui.log`
5. **Network không được đợi** - ứng dụng sẽ tự xử lý kết nối sau khi khởi động

---

## 10. Hỗ trợ

Nếu gặp vấn đề:

1. Xem log: `tail -f logs/gui.log`
2. Xem systemd log: `sudo journalctl -u aichat-gui.service -n 100`
3. Test chạy thủ công: `./scripts/run_gui_desktop.sh`
4. Kiểm tra quyền: `ls -la scripts/`

---

**Chúc bạn thành công! 🎉**
