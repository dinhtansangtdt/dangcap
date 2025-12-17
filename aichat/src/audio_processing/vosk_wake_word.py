"""
Wake Word Detector sử dụng Vosk STT để phát hiện "Bạn ơi"
"""
import asyncio
import json
import queue
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from src.constants.constants import AudioConfig
from src.utils.config_manager import ConfigManager
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Kiểm tra Vosk có được cài đặt không
try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    logger.warning("Vosk chưa được cài đặt. Chạy: pip install vosk")


class VoskWakeWordDetector:
    """
    Phát hiện wake word "Bạn ơi" sử dụng Vosk STT cục bộ.
    """

    def __init__(self):
        self.audio_codec = None
        self.is_running_flag = False
        self.paused = False
        self.detection_task = None
        self._main_loop = None  # Lưu main event loop

        # Audio queue - dùng threading.Queue vì on_audio_data được gọi từ thread khác
        self._audio_queue = queue.Queue(maxsize=100)

        # Chống trigger liên tục
        self.last_detection_time = 0
        self.detection_cooldown = 2.0  # 2 giây cooldown

        # Callbacks
        self.on_detected_callback: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

        # Vosk components
        self.model = None
        self.recognizer = None

        # Config
        config = ConfigManager.get_instance()
        self.enabled = config.get_config("WAKE_WORD_OPTIONS.USE_WAKE_WORD", False)
        
        if not self.enabled:
            logger.info("Wake word đã tắt trong config")
            return

        if not VOSK_AVAILABLE:
            logger.error("Vosk không khả dụng, wake word bị tắt")
            self.enabled = False
            return

        # Wake phrase để phát hiện
        self.wake_phrases = ["hello"]
        
        # Khởi tạo Vosk model
        self._init_vosk_model(config)

    def _init_vosk_model(self, config):
        """Khởi tạo Vosk model"""
        try:
            model_path = config.get_config("WAKE_WORD_OPTIONS.VOSK_MODEL_PATH", "models/vosk-model-vi")
            
            # Tìm model path
            possible_paths = [
                Path(model_path),
                Path("models/vosk-model-vi"),
                Path("models/vosk-model-small-vi-0.22"),
                Path("vosk-model-vi"),
            ]
            
            model_dir = None
            for p in possible_paths:
                if p.exists() and p.is_dir():
                    model_dir = p
                    break
            
            if model_dir is None:
                logger.error(f"Không tìm thấy Vosk model. Vui lòng tải model tiếng Việt từ:")
                logger.error("https://alphacephei.com/vosk/models")
                logger.error("Giải nén vào thư mục 'models/vosk-model-vi'")
                self.enabled = False
                return

            logger.info(f"Đang tải Vosk model từ: {model_dir}")
            self.model = Model(str(model_dir))
            self.recognizer = KaldiRecognizer(self.model, AudioConfig.INPUT_SAMPLE_RATE)
            self.recognizer.SetWords(True)
            
            logger.info("Vosk Wake Word Detector khởi tạo thành công!")
            
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Vosk: {e}", exc_info=True)
            self.enabled = False

    def on_detected(self, callback: Callable):
        """Đăng ký callback khi phát hiện wake word"""
        self.on_detected_callback = callback

    def on_audio_data(self, audio_data: np.ndarray):
        """Nhận audio data từ AudioCodec (observer pattern)
        
        Lưu ý: Method này được gọi từ audio thread (không có event loop),
        nên phải dùng threading.Queue thay vì asyncio.Queue
        """
        if not self.enabled or not self.is_running_flag or self.paused:
            return

        try:
            # Dùng threading.Queue vì được gọi từ thread khác
            self._audio_queue.put_nowait(audio_data.copy())
        except queue.Full:
            try:
                self._audio_queue.get_nowait()
                self._audio_queue.put_nowait(audio_data.copy())
            except queue.Empty:
                pass

    async def start(self, audio_codec) -> bool:
        """Bắt đầu wake word detection"""
        if not self.enabled:
            logger.warning("Wake word không được bật")
            return False

        if not self.model or not self.recognizer:
            logger.error("Vosk model chưa được khởi tạo")
            return False

        try:
            # Lưu main event loop để đảm bảo detection loop chạy trong đúng loop
            try:
                self._main_loop = asyncio.get_running_loop()
                logger.info(f"[VOSK] Event loop: {type(self._main_loop).__name__}")
            except RuntimeError:
                logger.error("[VOSK] Không có running event loop!")
                return False

            self.audio_codec = audio_codec
            self.is_running_flag = True
            self.paused = False

            # Đăng ký nhận audio
            self.audio_codec.add_audio_listener(self)

            # Bắt đầu detection loop trong main event loop
            self.detection_task = asyncio.create_task(self._detection_loop())

            logger.info("Vosk Wake Word Detector đã bắt đầu!")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khởi động Vosk detector: {e}", exc_info=True)
            self.enabled = False
            return False

    async def _detection_loop(self):
        """Vòng lặp phát hiện wake word
        
        Chạy trong main event loop để có thể dùng asyncio
        """
        audio_buffer = b""
        
        # Đảm bảo đang chạy trong event loop
        try:
            loop = asyncio.get_running_loop()
            logger.debug(f"[VOSK] Detection loop chạy trong event loop: {type(loop).__name__}")
        except RuntimeError as e:
            logger.error(f"[VOSK] Detection loop không có event loop: {e}")
            return
        
        while self.is_running_flag:
            try:
                if self.paused:
                    await asyncio.sleep(0.1)
                    continue

                # Lấy audio từ queue (threading.Queue)
                try:
                    audio_data = self._audio_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.01)
                    continue

                if audio_data is None or len(audio_data) == 0:
                    continue

                # Chuyển đổi sang bytes
                if audio_data.dtype == np.float32:
                    audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
                elif audio_data.dtype == np.int16:
                    audio_bytes = audio_data.tobytes()
                else:
                    audio_bytes = audio_data.astype(np.int16).tobytes()

                # Đưa vào recognizer
                if self.recognizer.AcceptWaveform(audio_bytes):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").lower().strip()
                    
                    if text:
                        logger.info(f"[VOSK] Nhận diện: '{text}'")
                        await self._check_wake_word(text)
                # Không check partial result để tránh trigger sai

            except asyncio.CancelledError:
                logger.info("[VOSK] Detection loop bị cancel")
                break
            except RuntimeError as e:
                if "no running event loop" in str(e):
                    logger.error(f"[VOSK] Lỗi: không có event loop trong detection loop: {e}")
                    # Thử lấy lại event loop từ main_loop
                    if self._main_loop and not self._main_loop.is_closed():
                        logger.info("[VOSK] Thử tiếp tục với main_loop...")
                        await asyncio.sleep(0.1)
                    else:
                        logger.error("[VOSK] Main loop không có hoặc đã đóng, dừng detection")
                        break
                else:
                    logger.error(f"[VOSK] RuntimeError trong detection loop: {e}")
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"[VOSK] Lỗi trong detection loop: {e}", exc_info=True)
                await asyncio.sleep(0.1)

    async def _check_wake_word(self, text: str):
        """Kiểm tra xem text có chứa wake word không"""
        # Chống trigger liên tục
        current_time = time.time()
        if current_time - self.last_detection_time < self.detection_cooldown:
            return

        # Tách các từ trong text
        words = text.split()
        
        # Kiểm tra wake phrases - phải là từ riêng biệt, không phải substring
        for phrase in self.wake_phrases:
            # Kiểm tra phrase là từ riêng biệt trong text
            if phrase in words or text.strip() == phrase:
                logger.info(f"[WAKE] Phát hiện '{phrase}' trong: '{text}'")
                self.last_detection_time = current_time
                
                # Reset recognizer để tránh lặp lại
                self.recognizer.Reset()
                
                # Gọi callback
                if self.on_detected_callback:
                    try:
                        if asyncio.iscoroutinefunction(self.on_detected_callback):
                            await self.on_detected_callback(phrase, text)
                        else:
                            self.on_detected_callback(phrase, text)
                    except Exception as e:
                        logger.error(f"Lỗi callback wake word: {e}")
                break

    async def stop(self):
        """Dừng detector"""
        self.is_running_flag = False

        if self.audio_codec:
            self.audio_codec.remove_audio_listener(self)

        if self.detection_task:
            self.detection_task.cancel()
            try:
                await self.detection_task
            except asyncio.CancelledError:
                pass

        # Clear queue
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break

        # Cleanup Vosk model để tránh nanobind leak
        try:
            if self.recognizer:
                self.recognizer = None
            if self.model:
                self.model = None
            logger.debug("[VOSK] Đã cleanup Vosk model")
        except Exception as e:
            logger.warning(f"[VOSK] Lỗi cleanup model: {e}")

        logger.info("Vosk Wake Word Detector đã dừng")

    def pause(self):
        """Tạm dừng detection"""
        self.paused = True

    def resume(self):
        """Tiếp tục detection"""
        self.paused = False

