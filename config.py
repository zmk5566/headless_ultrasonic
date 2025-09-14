#!/usr/bin/env python3
"""
配置管理
"""
import os
from pathlib import Path
from models import StreamConfig, AudioConfig

class Config:
    """应用配置"""
    
    # 服务器配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8380"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 数据目录
    DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
    
    @classmethod
    def get_stream_config(cls) -> StreamConfig:
        """获取默认流配置"""
        return StreamConfig(
            target_fps=int(os.getenv("TARGET_FPS", "30")),
            compression_level=int(os.getenv("COMPRESSION_LEVEL", "6")),
            enable_adaptive_fps=os.getenv("ADAPTIVE_FPS", "true").lower() == "true",
            min_fps=int(os.getenv("MIN_FPS", "5")),
            max_fps=int(os.getenv("MAX_FPS", "60")),
            magnitude_threshold_db=float(os.getenv("MAGNITUDE_THRESHOLD", "-80.0")),
            enable_smart_skip=os.getenv("SMART_SKIP", "false").lower() == "true",
            similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.95"))
        )
    
    @classmethod  
    def get_audio_config(cls) -> AudioConfig:
        """获取默认音频配置"""
        device_names = os.getenv("DEVICE_NAMES", "UltraMic384K,UltraMic,384K").split(",")
        fallback_device = os.getenv("FALLBACK_DEVICE")
        
        return AudioConfig(
            device_names=device_names,
            fallback_device_id=int(fallback_device) if fallback_device else None,
            sample_rate=int(os.getenv("SAMPLE_RATE", "384000")),
            channels=int(os.getenv("CHANNELS", "1")),
            blocksize=int(os.getenv("BLOCKSIZE", "3840")),
            fft_size=int(os.getenv("FFT_SIZE", "8192")),
            overlap=float(os.getenv("OVERLAP", "0.75")),
            window_type=os.getenv("WINDOW_TYPE", "hann"),
            threshold_db=float(os.getenv("THRESHOLD_DB", "-100.0"))
        )