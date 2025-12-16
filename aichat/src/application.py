import asyncio
import sys
import threading
from pathlib import Path
from typing import Any, Awaitable, Optional, Set

# 允许作为脚本直接运行：把项目根目录加入 sys.path（src 的上一级）
try:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
except Exception:
    pass

from src.constants.constants import DeviceState, ListeningMode
from src.plugins.calendar import CalendarPlugin
from src.plugins.iot import IoTPlugin
from src.plugins.manager import PluginManager
from src.plugins.mcp import McpPlugin
from src.plugins.shortcuts import ShortcutsPlugin
from src.plugins.ui import UIPlugin
from src.plugins.wake_word import WakeWordPlugin
from src.protocols.mqtt_protocol import MqttProtocol
from src.protocols.websocket_protocol import WebsocketProtocol
from src.utils.config_manager import ConfigManager
from src.utils.logging_config import get_logger
from src.utils.opus_loader import setup_opus

logger = get_logger(__name__)
setup_opus()


class Application:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = Application()
        return cls._instance

    def __init__(self):
        if Application._instance is not None:
            logger.error("尝试创建Application的多个实例")
            raise Exception("Application是单例类，请使用get_instance()获取实例")
        Application._instance = self

        logger.debug("初始化Application实例")

        # 配置
        self.config = ConfigManager.get_instance()

        # 状态
        self.running = False
        self.protocol = None

        # 设备状态（仅主程序改写，插件只读）
        self.device_state = DeviceState.IDLE
        try:
            aec_enabled_cfg = bool(self.config.get_config("AEC_OPTIONS.ENABLED", True))
        except Exception:
            aec_enabled_cfg = True
        self.aec_enabled = aec_enabled_cfg
        self.listening_mode = (
            ListeningMode.REALTIME if self.aec_enabled else ListeningMode.AUTO_STOP
        )
        self.keep_listening = False

        # 统一任务池（替代 _main_tasks/_bg_tasks）
        self._tasks: Set[asyncio.Task] = set()

        # 关停事件
        self._shutdown_event: Optional[asyncio.Event] = None

        # 事件循环
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None

        # 并发控制
        self._state_lock: Optional[asyncio.Lock] = None
        self._connect_lock: Optional[asyncio.Lock] = None

        # 插件
        self.plugins = PluginManager()

    # -------------------------
    # 生命周期
    # -------------------------
    async def run(self, *, protocol: str = "websocket", mode: str = "gui") -> int:
        logger.info("启动Application，protocol=%s", protocol)
        try:
            self.running = True
            self._main_loop = asyncio.get_running_loop()
            self._initialize_async_objects()
            self._set_protocol(protocol)
            self._setup_protocol_callbacks()
            # 插件：setup（延迟导入AudioPlugin，确保上面setup_opus已执行）
            from src.plugins.audio import AudioPlugin

            # 注册音频、UI、MCP、IoT、唤醒词、快捷键与日程插件（UI模式从run参数传入）
            # 插件会自动按 priority 排序：
            # AudioPlugin(10) -> McpPlugin(20) -> WakeWordPlugin(30) -> CalendarPlugin(40)
            # -> IoTPlugin(50) -> UIPlugin(60) -> ShortcutsPlugin(70)
            self.plugins.register(
                McpPlugin(),
                IoTPlugin(),
                AudioPlugin(),
                WakeWordPlugin(),
                CalendarPlugin(),
                UIPlugin(mode=mode),
                ShortcutsPlugin(),
            )
            await self.plugins.setup_all(self)
            # 启动后广播初始状态，确保 UI 就绪时能看到"待命"
            try:
                await self.plugins.notify_device_state_changed(self.device_state)
            except Exception:
                pass
            # Kết nối sẵn API ngay khi khởi động
            await self.connect_protocol()
            # 插件：start
            await self.plugins.start_all()
            # 等待关停
            await self._wait_shutdown()
            return 0

        except Exception as e:
            logger.error(f"应用运行失败: {e}", exc_info=True)
            return 1
        finally:
            try:
                await self.shutdown()
            except Exception as e:
                logger.error(f"关闭应用时出错: {e}")

    async def connect_protocol(self):
        """
        确保协议通道打开并广播一次协议就绪。返回是否已打开。
        """
        # 已打开直接返回
        try:
            if self.is_audio_channel_opened():
                return True
            if not self._connect_lock:
                # 未初始化锁时，直接尝试一次
                opened = await asyncio.wait_for(
                    self.protocol.open_audio_channel(), timeout=12.0
                )
                if not opened:
                    logger.error("协议连接失败")
                    return False
                logger.info("协议连接已建立，按Ctrl+C退出")
                await self.plugins.notify_protocol_connected(self.protocol)
                return True

            async with self._connect_lock:
                if self.is_audio_channel_opened():
                    return True
                opened = await asyncio.wait_for(
                    self.protocol.open_audio_channel(), timeout=12.0
                )
                if not opened:
                    logger.error("协议连接失败")
                    return False
                logger.info("协议连接已建立，按Ctrl+C退出")
                await self.plugins.notify_protocol_connected(self.protocol)
                return True
        except asyncio.TimeoutError:
            logger.error("协议连接超时")
            return False

    def _initialize_async_objects(self) -> None:
        logger.debug("初始化异步对象")
        self._shutdown_event = asyncio.Event()
        self._state_lock = asyncio.Lock()
        self._connect_lock = asyncio.Lock()

    def _set_protocol(self, protocol_type: str) -> None:
        logger.debug("设置协议类型: %s", protocol_type)
        if protocol_type == "mqtt":
            self.protocol = MqttProtocol(asyncio.get_running_loop())
        else:
            self.protocol = WebsocketProtocol()

    # -------------------------
    # 手动聆听（按住说话）
    # -------------------------
    async def start_listening_manual(self) -> None:
        try:
            ok = await self.connect_protocol()
            if not ok:
                return
            self.keep_listening = False

            # 如果说话中发送打断
            if self.device_state == DeviceState.SPEAKING:
                logger.info("说话中发送打断")
                await self.protocol.send_abort_speaking(None)
                await self.set_device_state(DeviceState.IDLE)
            await self.protocol.send_start_listening(ListeningMode.MANUAL)
            await self.set_device_state(DeviceState.LISTENING)
        except Exception:
            pass

    async def stop_listening_manual(self) -> None:
        try:
            await self.protocol.send_stop_listening()
            await self.set_device_state(DeviceState.IDLE)
        except Exception:
            pass

    # -------------------------
    # 自动/实时对话：根据 AEC 与当前配置选择模式，开启保持会话
    # -------------------------
    async def start_auto_conversation(self) -> None:
        try:
            ok = await self.connect_protocol()
            if not ok:
                return

            mode = (
                ListeningMode.REALTIME if self.aec_enabled else ListeningMode.AUTO_STOP
            )
            self.listening_mode = mode
            self.keep_listening = True
            await self.protocol.send_start_listening(mode)
            await self.set_device_state(DeviceState.LISTENING)
        except Exception:
            pass

    async def _start_conversation_from_wake_word(self) -> None:
        """
        Bắt đầu trò chuyện tự động khi phát hiện "Bạn ơi" từ STT.
        """
        try:
            # Nếu đang nói, dừng lại trước
            if self.device_state == DeviceState.SPEAKING:
                logger.info("Đang nói, gửi tín hiệu ngắt để bắt đầu trò chuyện mới")
                await self.protocol.send_abort_speaking(None)
                await self.set_device_state(DeviceState.IDLE)

            # Bắt đầu trò chuyện tự động
            mode = (
                ListeningMode.REALTIME if self.aec_enabled else ListeningMode.AUTO_STOP
            )
            self.listening_mode = mode
            self.keep_listening = True
            await self.protocol.send_start_listening(mode)
            await self.set_device_state(DeviceState.LISTENING)
            logger.info("Đã bắt đầu trò chuyện tự động sau khi phát hiện 'Bạn ơi'")
        except Exception as e:
            logger.error(f"Lỗi khi bắt đầu trò chuyện từ wake word: {e}", exc_info=True)

    def _setup_protocol_callbacks(self) -> None:
        self.protocol.on_network_error(self._on_network_error)
        self.protocol.on_incoming_json(self._on_incoming_json)
        self.protocol.on_incoming_audio(self._on_incoming_audio)
        self.protocol.on_audio_channel_opened(self._on_audio_channel_opened)
        self.protocol.on_audio_channel_closed(self._on_audio_channel_closed)

    async def _wait_shutdown(self) -> None:
        await self._shutdown_event.wait()

    # -------------------------
    # 统一任务管理（精简）
    # -------------------------
    def spawn(self, coro: Awaitable[Any], name: str) -> asyncio.Task:
        """
        创建任务并登记，关停时统一取消。
        """
        if not self.running or (self._shutdown_event and self._shutdown_event.is_set()):
            logger.debug(f"跳过任务创建（应用正在关闭）: {name}")
            return None
        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)

        def _done(t: asyncio.Task):
            self._tasks.discard(t)
            if not t.cancelled() and t.exception():
                logger.error(f"任务 {name} 异常结束: {t.exception()}", exc_info=True)

        task.add_done_callback(_done)
        return task

    def schedule_command_nowait(self, fn, *args, **kwargs) -> None:
        if not self._main_loop or self._main_loop.is_closed():
            logger.warning("主事件循环未就绪，拒绝调度")
            return

        def _runner():
            try:
                res = fn(*args, **kwargs)
                if asyncio.iscoroutine(res):
                    self.spawn(res, name=f"call:{getattr(fn, '__name__', 'anon')}")
            except Exception as e:
                logger.error(f"调度的可调用执行失败: {e}", exc_info=True)

        # 确保在事件循环线程里执行
        self._main_loop.call_soon_threadsafe(_runner)

    # -------------------------
    # 协议回调
    # -------------------------
    def _on_network_error(self, error_message=None):
        if error_message:
            logger.error(error_message)

        self.keep_listening = False
        # 出错即请求关闭
        # if self._shutdown_event and not self._shutdown_event.is_set():
        #     self._shutdown_event.set()

    def _on_incoming_audio(self, data: bytes):
        logger.debug(f"收到二进制消息，长度: {len(data)}")
        # 转发给插件
        self.spawn(self.plugins.notify_incoming_audio(data), "plugin:on_audio")

    def _on_incoming_json(self, json_data):
        try:
            msg_type = json_data.get("type") if isinstance(json_data, dict) else None
            logger.info(f"Nhận JSON: type={msg_type}, data={json_data}")
            
            # Xử lý goodbye - không đóng kết nối, chỉ về IDLE để chờ "Bạn ơi"
            if msg_type == "goodbye":
                logger.info("Server gửi goodbye, chuyển về IDLE và chờ 'Bạn ơi'...")
                self.keep_listening = False
                
                async def _handle_goodbye():
                    try:
                        await self.set_device_state(DeviceState.IDLE)
                        # KHÔNG gửi start_listening - chỉ giữ kết nối để chờ "Bạn ơi"
                        logger.info("Đã về IDLE, chờ 'Bạn ơi' để bắt đầu cuộc trò chuyện mới...")
                    except Exception as e:
                        logger.error(f"Lỗi xử lý goodbye: {e}")
                
                self.spawn(_handle_goodbye(), "handle_goodbye")
                return  # Không chuyển tiếp goodbye cho plugin
            
            # Phát hiện "Bạn ơi" từ STT để bắt đầu trò chuyện tự động
            if msg_type == "stt":
                text = json_data.get("text", "")
                logger.info(f"[STT] Nhận được text: '{text}', trạng thái hiện tại: {self.device_state}")
                # Chỉ kiểm tra khi đang ở trạng thái IDLE (chờ lệnh)
                if text and self.device_state == DeviceState.IDLE:
                    text_lower = text.lower().strip()
                    logger.info(f"[STT] Kiểm tra wake word trong: '{text_lower}'")
                    # Kiểm tra các biến thể của "bạn ơi"
                    wake_phrases = ["bạn ơi", "ban oi", "bạn oi", "ban ơi"]
                    for phrase in wake_phrases:
                        if phrase in text_lower:
                            logger.info(f"[WAKE] Phát hiện '{phrase}' trong STT: {text}, bắt đầu trò chuyện tự động")
                            self.spawn(
                                self._start_conversation_from_wake_word(),
                                "wake_word:stt_detected"
                            )
                            break
                elif text and self.device_state != DeviceState.IDLE:
                    logger.info(f"[STT] Bỏ qua vì không ở trạng thái IDLE (hiện tại: {self.device_state})")
            
            # 将 TTS start/stop 映射为设备状态（支持自动/实时，且不污染手动模式）
            if msg_type == "tts":
                state = json_data.get("state")
                if state == "start":
                    # 仅当保持会话且实时模式时，TTS开始期间保持LISTENING；否则显示SPEAKING
                    if (
                        self.keep_listening
                        and self.listening_mode == ListeningMode.REALTIME
                    ):
                        self.spawn(
                            self.set_device_state(DeviceState.LISTENING),
                            "state:tts_start_rt",
                        )
                    else:
                        self.spawn(
                            self.set_device_state(DeviceState.SPEAKING),
                            "state:tts_start_speaking",
                        )
                elif state == "stop":
                    if self.keep_listening:
                        # 继续对话：根据当前模式重启监听
                        async def _restart_listening():
                            try:
                                # 先设置状态为 LISTENING，触发音频队列清空和硬件停止等待
                                await self.set_device_state(DeviceState.LISTENING)

                                # 等待音频硬件完全停止后，再发送监听指令
                                # REALTIME 且已在 LISTENING 时无需重复发送
                                if not (
                                    self.listening_mode == ListeningMode.REALTIME
                                    and self.device_state == DeviceState.LISTENING
                                ):
                                    await self.protocol.send_start_listening(
                                        self.listening_mode
                                    )
                            except Exception:
                                pass

                        self.spawn(_restart_listening(), "state:tts_stop_restart")
                    else:
                        # Cuộc trò chuyện kết thúc -> về IDLE để chờ "Bạn ơi"
                        # KHÔNG gửi start_listening để tránh server tự động nhận lệnh
                        self.spawn(
                            self.set_device_state(DeviceState.IDLE),
                            "state:tts_stop_idle",
                        )
                        logger.info("Cuộc trò chuyện kết thúc, chờ 'Bạn ơi' để bắt đầu lại...")
            # 转发给插件
            self.spawn(self.plugins.notify_incoming_json(json_data), "plugin:on_json")
        except Exception:
            logger.info("收到JSON消息")

    async def _on_audio_channel_opened(self):
        logger.info("Kênh giao thức đã mở")
        # Kênh mở xong -> vào IDLE
        # Chờ người dùng nhấn Ctrl+K hoặc nút "Bắt đầu trò chuyện" để bắt đầu
        await self.set_device_state(DeviceState.IDLE)
        logger.info("Sẵn sàng! Nhấn Ctrl+K hoặc nút 'Bắt đầu trò chuyện' để bắt đầu")

    async def _on_audio_channel_closed(self):
        logger.info("Kênh giao thức đã đóng")
        # Kênh đóng -> về IDLE
        await self.set_device_state(DeviceState.IDLE)
        
        # Tự động kết nối lại để tiếp tục chờ "Bạn ơi"
        if self.running and not self._shutdown_event.is_set():
            logger.info("Đang kết nối lại để chờ 'Bạn ơi'...")
            await asyncio.sleep(1)  # Đợi 1 giây trước khi kết nối lại
            try:
                await self.connect_protocol()
            except Exception as e:
                logger.error(f"Lỗi kết nối lại: {e}")

    async def set_device_state(self, state: DeviceState):
        """
        仅供主程序内部调用：设置设备状态。插件请只读获取。
        """
        # print(f"set_device_state: {state}")
        if not self._state_lock:
            self.device_state = state
            try:
                await self.plugins.notify_device_state_changed(state)
            except Exception:
                pass
            return
        async with self._state_lock:
            if self.device_state == state:
                return
            logger.info(f"Đặt trạng thái thiết bị: {state}")
            self.device_state = state
        # Phát thông báo ngoài lock để tránh chặn callback plugin
        try:
            await self.plugins.notify_device_state_changed(state)
            if state == DeviceState.LISTENING:
                await asyncio.sleep(0.5)
                self.aborted = False
            # Reset aborted khi về IDLE để có thể capture audio cho STT
            if state == DeviceState.IDLE:
                self.aborted = False
        except Exception:
            pass

    # -------------------------
    # 只读访问器（提供给插件使用）
    # -------------------------
    def get_device_state(self):
        return self.device_state

    def is_idle(self) -> bool:
        return self.device_state == DeviceState.IDLE

    def is_listening(self) -> bool:
        return self.device_state == DeviceState.LISTENING

    def is_speaking(self) -> bool:
        return self.device_state == DeviceState.SPEAKING

    def get_listening_mode(self):
        return self.listening_mode

    def is_keep_listening(self) -> bool:
        return bool(self.keep_listening)

    def is_audio_channel_opened(self) -> bool:
        try:
            return bool(self.protocol and self.protocol.is_audio_channel_opened())
        except Exception:
            return False

    def should_capture_audio(self) -> bool:
        try:
            # Khi LISTENING thì luôn capture audio
            if self.device_state == DeviceState.LISTENING and not self.aborted:
                return True

            # Khi IDLE và kênh audio đã mở, vẫn capture để gửi cho STT phát hiện "Bạn ơi"
            if self.device_state == DeviceState.IDLE and self.is_audio_channel_opened():
                return True

            return (
                self.device_state == DeviceState.SPEAKING
                and self.aec_enabled
                and self.keep_listening
                and self.listening_mode == ListeningMode.REALTIME
            )
        except Exception:
            return False

    def get_state_snapshot(self) -> dict:
        return {
            "device_state": self.device_state,
            "listening_mode": self.listening_mode,
            "keep_listening": bool(self.keep_listening),
            "audio_opened": self.is_audio_channel_opened(),
        }

    async def abort_speaking(self, reason):
        """
        Ngừng phát âm thanh.
        """

        if self.aborted:
            logger.debug(f"Đã ngừng rồi, bỏ qua yêu cầu trùng lặp: {reason}")
            return

        logger.info(f"Ngừng phát âm thanh, lý do: {reason}")
        self.aborted = True
        
        # Kiểm tra kết nối trước khi gửi
        if self.protocol and self.is_audio_channel_opened():
            await self.protocol.send_abort_speaking(reason)
        
        await self.set_device_state(DeviceState.IDLE)

    # -------------------------
    # UI 辅助：供插件或工具直接调用
    # -------------------------
    def set_chat_message(self, role, message: str) -> None:
        """将文本更新转发为 UI 可识别的 JSON 消息（复用 UIPlugin 的 on_incoming_json）。
        role: "assistant" | "user" 影响消息类型映射。
        """
        try:
            msg_type = "tts" if str(role).lower() == "assistant" else "stt"
        except Exception:
            msg_type = "tts"
        payload = {"type": msg_type, "text": message}
        # 通过插件事件总线异步派发
        self.spawn(self.plugins.notify_incoming_json(payload), "ui:text_update")

    def set_emotion(self, emotion: str) -> None:
        """
        设置情绪表情：通过 UIPlugin 的 on_incoming_json 路由。
        """
        payload = {"type": "llm", "emotion": emotion}
        self.spawn(self.plugins.notify_incoming_json(payload), "ui:emotion_update")

    # -------------------------
    # 关停
    # -------------------------
    async def shutdown(self):
        if not self.running:
            return
        logger.info("正在关闭Application...")
        self.running = False

        if self._shutdown_event is not None:
            self._shutdown_event.set()

        try:
            # 取消所有登记任务
            if self._tasks:
                for t in list(self._tasks):
                    if not t.done():
                        t.cancel()
                await asyncio.gather(*self._tasks, return_exceptions=True)
                self._tasks.clear()

            # 关闭协议（限时，避免阻塞退出）
            if self.protocol:
                try:
                    try:
                        self._main_loop.create_task(self.protocol.close_audio_channel())
                    except asyncio.TimeoutError:
                        logger.warning("关闭协议超时，跳过等待")
                except Exception as e:
                    logger.error(f"关闭协议失败: {e}")

            # 插件：stop/shutdown
            try:
                await self.plugins.stop_all()
            except Exception:
                pass
            try:
                await self.plugins.shutdown_all()
            except Exception:
                pass

            logger.info("Application 关闭完成")
        except Exception as e:
            logger.error(f"关闭应用时出错: {e}", exc_info=True)
