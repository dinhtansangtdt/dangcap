# Hướng dẫn tự động khởi động trên Raspberry Pi

## ✨ Tính năng mới: Tự động cấu hình WiFi

Ứng dụng sẽ tự động:
1. ✅ Kiểm tra kết nối internet khi khởi động
2. 📡 Nếu chưa có internet → Tự động phát WiFi hotspot
3. 🌐 Hiển thị web để nhập SSID/password WiFi
4. 🔄 Tự động reboot và kết nối WiFi
5. 🚀 Chạy ứng dụng khi đã có internet

**WiFi Hotspot mặc định:**
- SSID: `AIChat-Setup`
- Password: `aichat12345`
- IP: `192.168.4.1`

---

## Cách 1: Sử dụng Systemd Service (Khuyến nghị)

### Bước 1: Copy file service vào systemd

```bash
# Copy service file vào systemd
sudo cp scripts/aichat.service /etc/systemd/system/

# Chỉnh sửa đường dẫn trong file service nếu cần
sudo nano /etc/systemd/system/aichat.service
```

**Lưu ý:** Đảm bảo đường dẫn trong file service đúng với vị trí dự án của bạn:
- `WorkingDirectory=/home/pi/aichat` → Thay bằng đường dẫn thực tế
- `ExecStart=/home/pi/aichat/scripts/start_aichat.sh` → Thay bằng đường dẫn thực tế

### Bước 2: Chỉnh sửa script khởi động

```bash
# Chỉnh sửa script nếu cần
nano scripts/start_aichat.sh

# Cấp quyền thực thi
chmod +x scripts/start_aichat.sh
```

### Bước 3: Kích hoạt service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Kích hoạt service (tự động chạy khi boot)
sudo systemctl enable aichat.service

# Khởi động service ngay
sudo systemctl start aichat.service

# Kiểm tra trạng thái
sudo systemctl status aichat.service

# Xem log
sudo journalctl -u aichat.service -f
```

### Bước 4: Quản lý service

```bash
# Dừng service
sudo systemctl stop aichat.service

# Khởi động lại service
sudo systemctl restart aichat.service

# Tắt tự động khởi động
sudo systemctl disable aichat.service
```

---

## Cách 2: Sử dụng autostart (Đơn giản hơn)

### Bước 1: Tạo file autostart

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/aichat.desktop
```

### Bước 2: Thêm nội dung sau:

```ini
[Desktop Entry]
Type=Application
Name=AI Chat
Exec=/home/pi/aichat/scripts/start_aichat.sh
Icon=/home/pi/aichat/assets/icon.png
Terminal=false
Categories=Utility;
```

**Lưu ý:** Thay đường dẫn `/home/pi/aichat` bằng đường dẫn thực tế của bạn.

### Bước 3: Cấp quyền thực thi

```bash
chmod +x ~/.config/autostart/aichat.desktop
chmod +x /home/pi/aichat/scripts/start_aichat.sh
```

### Bước 4: Khởi động lại để test

```bash
sudo reboot
```

---

## Cách 3: Thêm vào .bashrc (Không khuyến nghị cho GUI)

Chỉ dùng nếu bạn muốn chạy CLI mode:

```bash
nano ~/.bashrc
```

Thêm dòng cuối cùng:
```bash
# Auto start AI Chat
cd /home/pi/aichat && python3 main.py --mode cli &
```

---

## Kiểm tra và xử lý lỗi

### Xem log ứng dụng:
```bash
tail -f logs/startup.log
tail -f logs/app.log
```

### Kiểm tra X server:
```bash
echo $DISPLAY  # Phải hiển thị :0
```

### Test chạy thủ công:
```bash
cd /home/pi/aichat
python3 main.py --mode gui --protocol websocket
```

### Nếu gặp lỗi permission:
```bash
sudo chown -R pi:pi /home/pi/aichat
chmod +x scripts/start_aichat.sh
```

---

## Tắt màn hình screensaver (Tùy chọn)

Để màn hình không tắt khi không dùng:

```bash
# Tắt screensaver
sudo systemctl disable lightdm.service
# Hoặc
xset s off
xset -dpms
xset s noblank
```

Thêm vào `~/.xprofile`:
```bash
xset s off
xset -dpms
xset s noblank
```

---

## Cài đặt dependencies cho WiFi Hotspot

Trước khi setup autostart, cần cài đặt các package:

```bash
sudo apt-get update
sudo apt-get install -y hostapd dnsmasq
```

## Cấp quyền cho scripts

```bash
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

## Lưu ý quan trọng

1. **Đảm bảo đã cài đặt đầy đủ dependencies:**
   ```bash
   pip3 install -r requirements.txt
   sudo apt-get install -y hostapd dnsmasq
   ```

2. **Đảm bảo đã kích hoạt thiết bị trước khi setup autostart:**
   ```bash
   python3 main.py --mode gui
   # Hoàn tất quy trình kích hoạt
   ```

3. **Kiểm tra kết nối mạng:** 
   - Nếu chưa có internet, ứng dụng sẽ tự động phát WiFi hotspot
   - Kết nối WiFi `AIChat-Setup` (password: `aichat12345`)
   - Truy cập `http://192.168.4.1` để nhập WiFi của bạn
   - Sau khi cấu hình, RPi sẽ tự động reboot và kết nối WiFi

4. **Nếu dùng virtual environment:** Đảm bảo script `start_aichat.sh` kích hoạt đúng venv.

5. **Port 80:** Web server cấu hình WiFi chạy trên port 80, đảm bảo không có service nào khác đang dùng port này.

## Xử lý sự cố WiFi Hotspot

### Nếu hotspot không hoạt động:

```bash
# Kiểm tra hostapd
sudo systemctl status hostapd

# Kiểm tra dnsmasq
sudo systemctl status dnsmasq

# Xem log
sudo journalctl -u hostapd -f
sudo journalctl -u dnsmasq -f
```

### Nếu muốn tắt hotspot thủ công:

```bash
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
```

### Nếu muốn reset WiFi config:

```bash
sudo rm /etc/wpa_supplicant/wpa_supplicant.conf
sudo reboot
```

