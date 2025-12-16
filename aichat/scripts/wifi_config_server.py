#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web server đơn giản để cấu hình WiFi
Chạy trên hotspot để người dùng nhập SSID và password WiFi
"""

import http.server
import socketserver
import urllib.parse
import json
import subprocess
import os
import sys
from pathlib import Path

# Port cho web server
PORT = 80

# File lưu WiFi config
CONFIG_FILE = Path("/tmp/wifi_config.json")


class WiFiConfigHandler(http.server.SimpleHTTPRequestHandler):
    """Handler cho web server cấu hình WiFi"""

    def do_GET(self):
        """Xử lý GET request - Hiển thị form nhập WiFi"""
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            html = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cấu hình WiFi - AI Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 400px;
            width: 100%;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            color: #667eea;
            font-size: 24px;
            margin-bottom: 10px;
        }
        .logo p {
            color: #666;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
            font-size: 14px;
        }
        input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        button:active {
            transform: translateY(0);
        }
        .message {
            margin-top: 20px;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            font-size: 14px;
            display: none;
        }
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>🔧 Cấu hình WiFi</h1>
            <p>Vui lòng nhập thông tin WiFi của bạn</p>
        </div>
        <form id="wifiForm">
            <div class="form-group">
                <label for="ssid">Tên WiFi (SSID):</label>
                <input type="text" id="ssid" name="ssid" required autocomplete="off">
            </div>
            <div class="form-group">
                <label for="password">Mật khẩu WiFi:</label>
                <input type="password" id="password" name="password" autocomplete="off">
            </div>
            <button type="submit">Kết nối WiFi</button>
        </form>
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p style="margin-top: 10px; color: #666;">Đang cấu hình...</p>
        </div>
        <div class="message" id="message"></div>
    </div>
    <script>
        document.getElementById('wifiForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const ssid = document.getElementById('ssid').value;
            const password = document.getElementById('password').value;
            const loading = document.getElementById('loading');
            const message = document.getElementById('message');
            
            // Hiển thị loading
            loading.style.display = 'block';
            message.style.display = 'none';
            
            try {
                const response = await fetch('/configure', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ ssid: ssid, password: password })
                });
                
                const data = await response.json();
                
                loading.style.display = 'none';
                message.style.display = 'block';
                
                if (data.success) {
                    message.className = 'message success';
                    message.textContent = '✅ Cấu hình thành công! Đang khởi động lại...';
                    setTimeout(() => {
                        window.location.href = '/rebooting';
                    }, 2000);
                } else {
                    message.className = 'message error';
                    message.textContent = '❌ Lỗi: ' + (data.error || 'Không thể cấu hình WiFi');
                }
            } catch (error) {
                loading.style.display = 'none';
                message.style.display = 'block';
                message.className = 'message error';
                message.textContent = '❌ Lỗi kết nối: ' + error.message;
            }
        });
    </script>
</body>
</html>
            """
            self.wfile.write(html.encode('utf-8'))
        elif self.path == "/rebooting":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="5">
    <title>Đang khởi động lại...</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background: #f5f5f5;
        }
        .message {
            background: white;
            padding: 30px;
            border-radius: 10px;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="message">
        <h2>🔄 Đang khởi động lại...</h2>
        <p>Vui lòng đợi trong giây lát</p>
    </div>
</body>
</html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        """Xử lý POST request - Nhận WiFi config và lưu"""
        if self.path == "/configure":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                ssid = data.get('ssid', '').strip()
                password = data.get('password', '').strip()
                
                if not ssid:
                    self.send_json_response({"success": False, "error": "SSID không được để trống"})
                    return
                
                # Lưu config
                config = {
                    "ssid": ssid,
                    "password": password
                }
                
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(config, f)
                
                # Chạy script cấu hình WiFi
                script_path = Path(__file__).parent / "configure_wifi.sh"
                subprocess.Popen(
                    ["sudo", "bash", str(script_path), ssid, password],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                self.send_json_response({"success": True, "message": "Đang cấu hình WiFi..."})
                
            except Exception as e:
                self.send_json_response({"success": False, "error": str(e)})
        else:
            self.send_error(404)

    def send_json_response(self, data):
        """Gửi JSON response"""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        """Tắt log messages"""
        pass


def main():
    """Chạy web server"""
    try:
        with socketserver.TCPServer(("", PORT), WiFiConfigHandler) as httpd:
            print(f"🌐 WiFi Config Server đang chạy tại http://192.168.4.1")
            print("   Kết nối WiFi: AIChat-Setup / aichat12345")
            print("   Nhấn Ctrl+C để dừng")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Đã dừng server")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print("⚠️  Port 80 đã được sử dụng")
        else:
            print(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    main()

