# -*- coding: utf-8 -*-
"""
CLI模式设备激活流程 提供与GUI激活窗口相同的功能，但使用纯终端输出.
"""

from datetime import datetime
from typing import Optional

from src.core.system_initializer import SystemInitializer
from src.utils.device_activator import DeviceActivator
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class CLIActivation:
    """
    CLI模式设备激活处理器.
    """

    def __init__(self, system_initializer: Optional[SystemInitializer] = None):
        # 组件实例
        self.system_initializer = system_initializer
        self.device_activator: Optional[DeviceActivator] = None

        # 状态管理
        self.current_stage = None
        self.activation_data = None
        self.is_activated = False

        self.logger = logger

    async def run_activation_process(self) -> bool:
        """运行完整的CLI激活流程.

        Returns:
            bool: 激活是否成功
        """
        try:
            self._print_header()

            # 如果已经提供了SystemInitializer实例，直接使用
            if self.system_initializer:
                self._log_and_print("Sử dụng hệ thống đã khởi tạo")
                self._update_device_info()
                return await self._start_activation_process()
            else:
                # 否则创建新的实例并运行初始化
                self._log_and_print("Bắt đầu quy trình khởi tạo hệ thống")
                self.system_initializer = SystemInitializer()

                # 运行初始化流程
                init_result = await self.system_initializer.run_initialization()

                if init_result.get("success", False):
                    self._update_device_info()

                    # 显示状态消息
                    status_message = init_result.get("status_message", "")
                    if status_message:
                        self._log_and_print(status_message)

                    # 检查是否需要激活
                    if init_result.get("need_activation_ui", True):
                        return await self._start_activation_process()
                    else:
                        # 无需激活，直接完成
                        self.is_activated = True
                        self._log_and_print("Thiết bị đã được kích hoạt, không cần thao tác thêm")
                        return True
                else:
                    error_msg = init_result.get("error", "Khởi tạo thất bại")
                    self._log_and_print(f"Lỗi: {error_msg}")
                    return False

        except KeyboardInterrupt:
            self._log_and_print("\nNgười dùng ngắt quy trình kích hoạt")
            return False
        except Exception as e:
            self.logger.error(f"Lỗi quy trình kích hoạt CLI: {e}", exc_info=True)
            self._log_and_print(f"Lỗi kích hoạt: {e}")
            return False

    def _print_header(self):
        """
        打印CLI激活流程头部信息.
        """
        print("\n" + "=" * 60)
        print("Ứng dụng khách AI Tiểu Trí - Quy trình kích hoạt thiết bị")
        print("=" * 60)
        print("Đang khởi tạo thiết bị, vui lòng đợi...")
        print()

    def _update_device_info(self):
        """
        更新设备信息显示.
        """
        if (
            not self.system_initializer
            or not self.system_initializer.device_fingerprint
        ):
            return

        device_fp = self.system_initializer.device_fingerprint

        # 获取设备信息
        serial_number = device_fp.get_serial_number()
        mac_address = device_fp.get_mac_address_from_efuse()

        # 获取激活状态
        activation_status = self.system_initializer.get_activation_status()
        local_activated = activation_status.get("local_activated", False)
        server_activated = activation_status.get("server_activated", False)
        status_consistent = activation_status.get("status_consistent", True)

        # 更新激活状态
        self.is_activated = local_activated

        # 显示设备信息
        print("📱 Thông tin thiết bị:")
        print(f"   Số seri: {serial_number if serial_number else '--'}")
        print(f"   Địa chỉ MAC: {mac_address if mac_address else '--'}")

        # 显示激活状态
        if not status_consistent:
            if local_activated and not server_activated:
                status_text = "Trạng thái không nhất quán (cần kích hoạt lại)"
            else:
                status_text = "Trạng thái không nhất quán (đã tự động sửa)"
        else:
            status_text = "Đã kích hoạt" if local_activated else "Chưa kích hoạt"

        print(f"   Trạng thái kích hoạt: {status_text}")

    async def _start_activation_process(self) -> bool:
        """
        开始激活流程.
        """
        try:
            # 获取激活数据
            activation_data = self.system_initializer.get_activation_data()

            if not activation_data:
                self._log_and_print("\nKhông lấy được dữ liệu kích hoạt")
                print("Lỗi: Không lấy được dữ liệu kích hoạt, vui lòng kiểm tra kết nối mạng")
                return False

            self.activation_data = activation_data

            # 显示激活信息
            self._show_activation_info(activation_data)

            # 初始化设备激活器
            config_manager = self.system_initializer.get_config_manager()
            self.device_activator = DeviceActivator(config_manager)

            # 开始激活流程
            self._log_and_print("\nBắt đầu quy trình kích hoạt thiết bị...")
            print("Đang kết nối đến máy chủ kích hoạt, vui lòng giữ kết nối mạng...")

            activation_success = await self.device_activator.process_activation(
                activation_data
            )

            if activation_success:
                self._log_and_print("\nKích hoạt thiết bị thành công!")
                self._print_activation_success()
                return True
            else:
                self._log_and_print("\nKích hoạt thiết bị thất bại")
                self._print_activation_failure()
                return False

        except Exception as e:
            self.logger.error(f"Lỗi quy trình kích hoạt: {e}", exc_info=True)
            self._log_and_print(f"\nLỗi kích hoạt: {e}")
            return False

    def _show_activation_info(self, activation_data: dict):
        """
        显示激活信息.
        """
        code = activation_data.get("code", "------")
        message = activation_data.get("message", "Vui lòng truy cập xiaozhi.me để nhập mã xác thực")

        print("\n" + "=" * 60)
        print("Thông tin kích hoạt thiết bị")
        print("=" * 60)
        print(f"Mã xác thực kích hoạt: {code}")
        print(f"Hướng dẫn kích hoạt: {message}")
        print("=" * 60)

        # 格式化显示验证码（每个字符间加空格）
        formatted_code = " ".join(code)
        print(f"\nMã xác thực (vui lòng nhập trên trang web): {formatted_code}")
        print("\nVui lòng làm theo các bước sau để hoàn tất kích hoạt:")
        print("1. Mở trình duyệt và truy cập xiaozhi.me")
        print("2. Đăng nhập vào tài khoản của bạn")
        print("3. Chọn thêm thiết bị")
        print(f"4. Nhập mã xác thực: {formatted_code}")
        print("5. Xác nhận thêm thiết bị")
        print("\nĐang chờ xác nhận kích hoạt, vui lòng hoàn tất thao tác trên trang web...")

        self._log_and_print(f"激活验证码: {code}")
        self._log_and_print(f"激活说明: {message}")

    def _print_activation_success(self):
        """
        打印激活成功信息.
        """
        print("\n" + "=" * 60)
        print("Kích hoạt thiết bị thành công!")
        print("=" * 60)
        print("Thiết bị đã được thêm thành công vào tài khoản của bạn")
        print("Cấu hình đã được tự động cập nhật")
        print("Chuẩn bị khởi động ứng dụng khách AI Tiểu Trí...")
        print("=" * 60)

    def _print_activation_failure(self):
        """
        打印激活失败信息.
        """
        print("\n" + "=" * 60)
        print("Kích hoạt thiết bị thất bại")
        print("=" * 60)
        print("Nguyên nhân có thể:")
        print("• Kết nối mạng không ổn định")
        print("• Mã xác thực nhập sai hoặc đã hết hạn")
        print("• Máy chủ tạm thời không khả dụng")
        print("\nGiải pháp:")
        print("• Kiểm tra kết nối mạng")
        print("• Chạy lại chương trình để lấy mã xác thực mới")
        print("• Đảm bảo nhập đúng mã xác thực trên trang web")
        print("=" * 60)

    def _log_and_print(self, message: str):
        """
        同时记录日志和打印到终端.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.logger.info(message)

    def get_activation_result(self) -> dict:
        """
        获取激活结果.
        """
        device_fingerprint = None
        config_manager = None

        if self.system_initializer:
            device_fingerprint = self.system_initializer.device_fingerprint
            config_manager = self.system_initializer.config_manager

        return {
            "is_activated": self.is_activated,
            "device_fingerprint": device_fingerprint,
            "config_manager": config_manager,
        }
