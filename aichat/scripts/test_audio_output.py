#!/usr/bin/env python3
"""
Script test audio output để kiểm tra có nghe được âm thanh không
"""
import asyncio
import sys
from pathlib import Path

# Thêm thư mục dự án vào path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from src.audio_codecs.audio_codec import AudioCodec
from src.utils.logging_config import setup_logging, get_logger

logger = get_logger(__name__)


async def test_audio_output():
    """Test audio output"""
    logger.info("Bắt đầu test audio output...")
    
    try:
        # Khởi tạo AudioCodec
        codec = AudioCodec()
        await codec.initialize()
        
        logger.info("AudioCodec đã được khởi tạo")
        logger.info(f"Output device: {codec.speaker_device_id}")
        logger.info(f"Output sample rate: {codec.device_output_sample_rate}Hz")
        logger.info(f"Output channels: {codec.output_channels}")
        logger.info(f"Output stream active: {codec.output_stream.active if codec.output_stream else False}")
        
        if not codec.output_stream or not codec.output_stream.active:
            logger.error("❌ Output stream không active!")
            logger.error("Có thể cần:")
            logger.error("1. Kiểm tra audio device trong Settings")
            logger.error("2. Kiểm tra quyền audio (pulseaudio/alsa)")
            logger.error("3. Thử reinitialize: await codec.reinitialize_stream(is_input=False)")
            return False
        
        # Tạo test tone (440Hz, 1 giây)
        import numpy as np
        sample_rate = 24000
        duration = 1.0
        frequency = 440.0
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        tone = np.sin(2 * np.pi * frequency * t)
        tone_int16 = (tone * 32767).astype(np.int16)
        
        # Chia thành frames
        frame_size = 480  # 20ms @ 24kHz
        logger.info(f"Đang phát test tone ({frequency}Hz, {duration}s)...")
        
        for i in range(0, len(tone_int16), frame_size):
            frame = tone_int16[i:i+frame_size]
            if len(frame) < frame_size:
                # Pad với zeros
                padded = np.zeros(frame_size, dtype=np.int16)
                padded[:len(frame)] = frame
                frame = padded
            
            await codec.write_pcm_direct(frame)
            await asyncio.sleep(0.02)  # 20ms
        
        logger.info("✅ Test tone đã phát xong")
        await asyncio.sleep(0.5)
        
        # Cleanup
        await codec.close()
        logger.info("✅ Test hoàn tất")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test audio output thất bại: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    setup_logging()
    result = asyncio.run(test_audio_output())
    sys.exit(0 if result else 1)
