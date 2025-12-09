from typing import Any

from src.constants.constants import AbortReason
from src.plugins.base import Plugin
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class WakeWordPlugin(Plugin):
    name = "wake_word"
    priority = 30  # Phụ thuộc AudioPlugin

    def __init__(self) -> None:
        super().__init__()
        self.app = None
        self.detector = None

    async def setup(self, app: Any) -> None:
        self.app = app
        
        # Thử Vosk trước (STT cục bộ, miễn phí)
        detector = self._try_vosk_detector()
        
        # Nếu Vosk không khả dụng, thử Sherpa-ONNX
        if detector is None:
            detector = self._try_sherpa_detector()
        
        if detector is None:
            logger.info("Không có wake word detector khả dụng")
            return
            
        self.detector = detector
        self.detector.on_detected(self._on_detected)
        if hasattr(self.detector, 'on_error'):
            self.detector.on_error = self._on_error
        
        logger.info(f"Wake word detector: {type(self.detector).__name__}")

    def _try_vosk_detector(self):
        """Thử khởi tạo Vosk Wake Word Detector"""
        try:
            from src.audio_processing.vosk_wake_word import VoskWakeWordDetector
            
            detector = VoskWakeWordDetector()
            if getattr(detector, "enabled", False):
                logger.info("Sử dụng Vosk Wake Word Detector")
                return detector
        except ImportError as e:
            logger.debug(f"Vosk không khả dụng: {e}")
        except Exception as e:
            logger.debug(f"Lỗi khởi tạo Vosk: {e}")
        return None

    def _try_sherpa_detector(self):
        """Thử khởi tạo Sherpa-ONNX Wake Word Detector"""
        try:
            from src.audio_processing.wake_word_detect import WakeWordDetector

            detector = WakeWordDetector()
            if getattr(detector, "enabled", False):
                logger.info("Sử dụng Sherpa-ONNX Wake Word Detector")
                return detector
        except ImportError as e:
            logger.debug(f"Sherpa-ONNX không khả dụng: {e}")
        except Exception as e:
            logger.debug(f"Lỗi khởi tạo Sherpa-ONNX: {e}")
        return None

    async def start(self) -> None:
        if not self.detector:
            return
        try:
            # 需要音频编码器以提供原始PCM数据
            audio_codec = getattr(self.app, "audio_codec", None)
            if audio_codec is None:
                logger.warning("未找到audio_codec，无法启动唤醒词检测")
                return
            await self.detector.start(audio_codec)
        except Exception as e:
            logger.error(f"启动唤醒词检测器失败: {e}", exc_info=True)

    async def stop(self) -> None:
        if self.detector:
            try:
                await self.detector.stop()
            except Exception as e:
                logger.warning(f"停止唤醒词检测器失败: {e}")

    async def shutdown(self) -> None:
        if self.detector:
            try:
                await self.detector.stop()
            except Exception as e:
                logger.warning(f"关闭唤醒词检测器失败: {e}")

    async def _on_detected(self, wake_word, full_text):
        # Phát hiện wake word: bắt đầu trò chuyện tự động
        logger.info(f"[WAKE_WORD_PLUGIN] Phát hiện wake word: '{wake_word}', full_text: '{full_text}'")
        try:
            # Chỉ xử lý khi đang ở trạng thái IDLE
            if hasattr(self.app, "device_state") and hasattr(self.app, "start_auto_conversation"):
                if self.app.is_idle():
                    logger.info("[WAKE_WORD_PLUGIN] Đang IDLE, bắt đầu trò chuyện tự động...")
                    
                    # Kết nối protocol trước
                    if await self.app.connect_protocol():
                        # Gửi "Xin chào" cho AI Xiaozhi để nó phản hồi thông báo
                        await self.app.protocol.send_wake_word_detected("Xin chào")
                        logger.info("[WAKE_WORD_PLUGIN] Đã gửi 'Xin chào' cho AI Xiaozhi")
                        
                        # Bắt đầu cuộc trò chuyện tự động (keep_listening = True)
                        await self.app.start_auto_conversation()
                        logger.info("[WAKE_WORD_PLUGIN] Đã bắt đầu cuộc trò chuyện tự động")
                    
                elif self.app.is_speaking():
                    logger.info("[WAKE_WORD_PLUGIN] Đang nói, ngắt và bắt đầu lại...")
                    await self.app.abort_speaking(AbortReason.WAKE_WORD_DETECTED)
                    audio_plugin = self.app.plugins.get_plugin("audio")
                    if audio_plugin and audio_plugin.codec:
                        await audio_plugin.codec.clear_audio_queue()
                else:
                    logger.info(f"[WAKE_WORD_PLUGIN] Bỏ qua vì trạng thái: {self.app.device_state}")
        except Exception as e:
            logger.error(f"Lỗi xử lý wake word: {e}", exc_info=True)

    def _on_error(self, error):
        try:
            logger.error(f"唤醒词检测错误: {error}")
            if hasattr(self.app, "set_chat_message"):
                self.app.set_chat_message("assistant", f"[唤醒词错误] {error}")
        except Exception as e:
            logger.error(f"处理唤醒词错误回调失败: {e}")
