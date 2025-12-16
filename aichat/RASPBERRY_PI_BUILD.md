# Hướng dẫn đóng gói XiaoZhi AI cho Raspberry Pi 3B+

## Yêu cầu hệ thống

- **Raspberry Pi 3B+** với Raspberry Pi OS **32-bit (armhf)**
- Python 3.9+ 
- Ít nhất 2GB RAM (swap nếu cần)
- Ít nhất 8GB dung lượng trống

> ⚠️ **Lưu ý**: Hướng dẫn này dành cho **Raspberry Pi OS 32-bit (armhf)**. Code đã được cập nhật để hỗ trợ kiến trúc armhf.

## Bước 1: Chuẩn bị môi trường trên Raspberry Pi

```bash
# Cập nhật hệ thống
sudo apt update && sudo apt upgrade -y

# Cài đặt các dependencies hệ thống
sudo apt install -y build-essential python3-dev python3-pip python3-venv \
    libopenblas-dev liblapack-dev gfortran patchelf \
    libportaudio2 libportaudiocpp0 portaudio19-dev \
    libopus0 libopus-dev \
    libasound2-dev \
    dpkg-dev fakeroot

# Cài đặt PyQt5 qua apt (nếu cần GUI)
sudo apt install -y python3-pyqt5

# Cài đặt OpenCV qua apt (nhẹ hơn pip)
sudo apt install -y python3-opencv
```

## Bước 2: Tạo môi trường ảo Python

```bash
# Tạo virtual environment
python3 -m venv ~/xiaozhi-env
source ~/xiaozhi-env/bin/activate

# Nâng cấp pip
pip install --upgrade pip wheel setuptools
```

## Bước 3: Clone và cài đặt dự án

```bash
# Clone dự án (hoặc copy từ máy khác)
cd ~
git clone <your-repo-url> xiaozhi
cd xiaozhi

# Cài đặt dependencies cho Raspberry Pi
pip install -r requirements_rpi.txt

# Cài đặt các package đặc biệt cho ARM
pip install pyinstaller
```

## Bước 4: Cài đặt UnifyPy

```bash
pip install unifypy
```

## Bước 5: Cài đặt thư viện native cho armhf (32-bit)

⚠️ **Quan trọng**: Dự án chỉ có thư viện cho `arm64`, bạn cần tạo thư viện cho `armhf`:

```bash
# Cài đặt thư viện hệ thống
sudo apt install -y libopus0 libopus-dev

# Tạo thư mục cho armhf
mkdir -p libs/libopus/linux/armhf
mkdir -p libs/webrtc_apm/linux/armhf

# Tạo symlink từ thư viện hệ thống
ln -sf /usr/lib/arm-linux-gnueabihf/libopus.so.0 libs/libopus/linux/armhf/libopus.so
```

### Cập nhật opus_loader.py để nhận diện armhf

Kiểm tra file `src/utils/opus_loader.py` và đảm bảo nó hỗ trợ kiến trúc `armhf`:

```python
# Thêm mapping cho armhf nếu chưa có
if machine in ('armv7l', 'armhf'):
    arch = 'armhf'
```

### Về webrtc_apm cho armhf

Nếu cần WebRTC AEC, bạn phải compile từ source:

```bash
# Clone và build webrtc_apm cho armhf
# Hoặc tạm thời disable AEC trong config
```

## Bước 6: Đóng gói với UnifyPy

### Cách 1: Sử dụng cấu hình có sẵn

```bash
# Kích hoạt môi trường
source ~/xiaozhi-env/bin/activate
cd ~/xiaozhi

# Đóng gói với cấu hình cho Raspberry Pi
unifypy . --config build_rpi.json --verbose

# Hoặc clean build
unifypy . --config build_rpi.json --clean --verbose
```

### Cách 2: Sử dụng wizard tương tác

```bash
unifypy . --init
```

Chọn các tùy chọn:
- Platform: Linux
- Format: DEB
- Architecture: armhf hoặc arm64
- Windowed: No (CLI mode)

## Bước 7: Kết quả đóng gói

Sau khi hoàn tất, bạn sẽ có:

```
dist/
├── xiaozhi/           # Thư mục chứa executable
│   ├── xiaozhi        # File thực thi chính
│   ├── models/
│   ├── libs/
│   └── ...
└── installer/
    └── xiaozhi-1.1.9.deb   # Package DEB để cài đặt
```

## Bước 8: Cài đặt và chạy

```bash
# Cài đặt package DEB
sudo dpkg -i dist/installer/xiaozhi-*.deb

# Hoặc chạy trực tiếp
./dist/xiaozhi/xiaozhi --mode cli --protocol websocket
```

## Chế độ chạy khuyến nghị cho Raspberry Pi

Do Raspberry Pi 3B+ có tài nguyên hạn chế, khuyến nghị:

```bash
# Chạy ở chế độ CLI (nhẹ hơn GUI)
./xiaozhi --mode cli --protocol websocket

# Hoặc với MQTT
./xiaozhi --mode cli --protocol mqtt
```

## Khắc phục sự cố

### Lỗi thiếu thư viện

```bash
# Kiểm tra dependencies
ldd dist/xiaozhi/xiaozhi

# Cài đặt thư viện thiếu
sudo apt install <library-name>
```

### Lỗi NumPy/SciPy compilation

```bash
# Sử dụng wheel có sẵn
pip install numpy --prefer-binary

# Hoặc cài từ piwheels (repo wheel cho RPi)
pip install numpy -i https://www.piwheels.org/simple
```

### Lỗi bộ nhớ khi build

```bash
# Tăng swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Đổi CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Lỗi PyInstaller

```bash
# Clean build
rm -rf build/ dist/ *.spec
unifypy . --config build_rpi.json --clean --verbose
```

## Tối ưu cho Raspberry Pi

1. **Sử dụng Raspberry Pi OS 64-bit** - Tương thích tốt hơn với các thư viện
2. **Chạy ở chế độ CLI** - Tiết kiệm RAM
3. **Sử dụng WebSocket** - Nhẹ hơn MQTT trong một số trường hợp
4. **Tắt wake word detection** - Nếu không cần, để tiết kiệm CPU

## Liên kết tham khảo

- [UnifyPy GitHub](https://github.com/example/unifypy)
- [PyInstaller Documentation](https://pyinstaller.org/)
- [Pi Wheels - Pre-built Python packages for RPi](https://www.piwheels.org/)

