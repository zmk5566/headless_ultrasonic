#!/usr/bin/env python3
"""
数据模型定义
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import numpy as np

class FFTFrame(BaseModel):
    """FFT数据帧"""
    timestamp: float                    # Unix时间戳（毫秒精度）
    sequence_id: int                   # 帧序列号
    sample_rate: int                   # 采样率
    fft_size: int                      # FFT大小
    data_compressed: str               # Base64编码的压缩FFT数据
    compression_method: str = "gzip"   # 压缩方法
    data_size_bytes: int              # 压缩后数据大小
    original_size_bytes: int          # 原始数据大小
    
    # 元数据
    peak_frequency_hz: float          # 峰值频率
    peak_magnitude_db: float          # 峰值幅度
    spl_db: float                     # 声压级
    fps: float                        # 当前帧率

class StreamConfig(BaseModel):
    """流配置"""
    target_fps: int = 30              # 目标帧率
    compression_level: int = 6        # gzip压缩级别 (1-9)
    enable_adaptive_fps: bool = True  # 自适应帧率
    min_fps: int = 5                  # 最小帧率
    max_fps: int = 60                 # 最大帧率
    magnitude_threshold_db: float = -80.0  # 幅度阈值，低于此值不发送
    enable_smart_skip: bool = False   # 智能跳帧（相似帧跳过）- 默认禁用以确保在安静环境中也能看到数据
    similarity_threshold: float = 0.95 # 相似度阈值

class AudioConfig(BaseModel):
    """音频配置"""
    device_names: List[str] = ["UltraMic384K", "UltraMic", "384K"]
    fallback_device_id: Optional[int] = None
    sample_rate: int = 384000
    channels: int = 1
    blocksize: int = 3840             # 10ms @ 384kHz
    fft_size: int = 8192
    overlap: float = 0.75
    window_type: str = "hann"
    threshold_db: float = -100.0      # dB阈值，低于此值将被忽略

class SystemStatus(BaseModel):
    """系统状态"""
    is_running: bool = False
    current_fps: float = 0.0
    connected_clients: int = 0
    total_frames_sent: int = 0
    total_bytes_sent: int = 0
    uptime_seconds: float = 0.0
    audio_device_name: Optional[str] = None
    last_error: Optional[str] = None
    device_disconnected: bool = False
    callback_health: str = "unknown"

class ControlResponse(BaseModel):
    """控制响应"""
    status: str = "success"
    message: Optional[str] = None
    timestamp: float
    
    @classmethod
    def success(cls, message: str = None) -> "ControlResponse":
        return cls(
            status="success",
            message=message,
            timestamp=datetime.now().timestamp() * 1000
        )
    
    @classmethod
    def error(cls, message: str) -> "ControlResponse":
        return cls(
            status="error", 
            message=message,
            timestamp=datetime.now().timestamp() * 1000
        )