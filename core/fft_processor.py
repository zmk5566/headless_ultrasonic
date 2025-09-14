#!/usr/bin/env python3
"""
FFT处理和数据压缩模块
从fast_ultrasonic.py的FFT处理逻辑改进而来
"""
import numpy as np
from scipy.signal import get_window
from collections import deque
import gzip
import base64
import time
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class FFTProcessor:
    """FFT处理器"""
    
    def __init__(self, 
                 sample_rate: int = 384000,
                 fft_size: int = 8192,
                 overlap: float = 0.75,
                 window_type: str = "hann",
                 compression_level: int = 6,
                 threshold_db: float = -100.0):
        
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.overlap = overlap
        self.window_type = window_type
        self.compression_level = compression_level
        self.threshold_db = threshold_db
        
        # 创建窗函数
        self.window = get_window(window_type, fft_size)
        
        # 音频数据缓冲区
        self.audio_buffer = deque(maxlen=fft_size * 2)
        
        # 频率轴
        self.freqs = np.fft.rfftfreq(fft_size, 1/sample_rate)
        self.freq_khz = self.freqs / 1000
        
        # 性能统计
        self.frames_processed = 0
        self.total_processing_time = 0.0
        self.last_fft_data = None
        
        # SPL历史用于平滑
        self.spl_history = deque(maxlen=30)
        
        logger.info(f"FFT处理器初始化完成:")
        logger.info(f"  采样率: {sample_rate} Hz")
        logger.info(f"  FFT大小: {fft_size}")
        logger.info(f"  窗函数: {window_type}")
        logger.info(f"  dB阈值: {threshold_db} dB (低于此值将被忽略)")
        logger.info(f"  频率分辨率: {sample_rate/fft_size:.2f} Hz")
        logger.info(f"  Nyquist频率: {sample_rate/2/1000:.1f} kHz")
        logger.info(f"  输出频率点数: {len(self.freq_khz)}")
    
    def add_audio_data(self, audio_data: np.ndarray):
        """添加音频数据到缓冲区"""
        self.audio_buffer.extend(audio_data)
    
    def can_process(self) -> bool:
        """检查是否有足够数据进行FFT"""
        return len(self.audio_buffer) >= self.fft_size
    
    def process_fft(self) -> Optional[Tuple[np.ndarray, dict]]:
        """处理FFT并返回结果和元数据"""
        if not self.can_process():
            return None
            
        start_time = time.time()
        
        try:
            # 计算步长（考虑重叠）
            hop_size = int(self.fft_size * (1 - self.overlap))
            
            # 获取FFT大小的数据从缓冲区开头
            data = np.array(list(self.audio_buffer)[:self.fft_size])
            
            # 移除已处理的数据（移除hop_size个样本以实现重叠）
            for _ in range(hop_size):
                if len(self.audio_buffer) > 0:
                    self.audio_buffer.popleft()
            
            # 应用窗函数
            windowed_data = data * self.window
            
            # FFT
            fft_result = np.fft.rfft(windowed_data)
            
            # 转换为dB - 使用与simple_ultrasonic.py相同的方法
            # 直接从FFT结果计算，不使用功率谱
            magnitude_db = 20 * np.log10(np.abs(fft_result) / self.fft_size + 1e-10)
            
            # 应用窗函数补偿
            magnitude_db += 6.0  # Hann窗的能量补偿 (20*log10(2) ≈ 6dB)
            
            # 应用dB阈值过滤 - 将低于阈值的值设为阈值
            magnitude_db = np.maximum(magnitude_db, self.threshold_db)
            
            # 计算元数据
            metadata = self._calculate_metadata(magnitude_db, data)
            
            # 更新统计
            self.frames_processed += 1
            self.total_processing_time += time.time() - start_time
            self.last_fft_data = magnitude_db
            
            return magnitude_db.astype(np.float32), metadata
            
        except Exception as e:
            logger.error(f"FFT处理出错: {e}")
            return None
    
    def _calculate_metadata(self, magnitude_db: np.ndarray, audio_data: np.ndarray) -> dict:
        """计算FFT元数据"""
        # 峰值频率和幅度
        peak_freq_idx = np.argmax(magnitude_db)
        peak_freq = self.freqs[peak_freq_idx]
        peak_magnitude = magnitude_db[peak_freq_idx]
        
        # 计算SPL
        spl = self._calculate_spl(audio_data)
        self.spl_history.append(spl)
        avg_spl = np.mean(list(self.spl_history)) if self.spl_history else spl
        
        return {
            "peak_frequency_hz": float(peak_freq),
            "peak_magnitude_db": float(peak_magnitude), 
            "spl_db": float(avg_spl),
            "processing_time_ms": (time.time() * 1000) - (time.time() * 1000)  # 实际会在调用时计算
        }
    
    def _calculate_spl(self, audio_data: np.ndarray) -> float:
        """计算声压级 (SPL)"""
        # 计算RMS值
        rms = np.sqrt(np.mean(audio_data**2))
        
        # 转换为dB SPL
        if rms > 0:
            spl_db = 20 * np.log10(rms) + 94  # 94dB参考偏移
        else:
            spl_db = 0
        
        return max(0.0, spl_db)
    
    def compress_fft_data(self, magnitude_db: np.ndarray) -> Tuple[str, int, int]:
        """压缩FFT数据
        
        Returns:
            (compressed_base64, compressed_size, original_size)
        """
        try:
            # 转为字节数据
            original_bytes = magnitude_db.astype(np.float32).tobytes()
            original_size = len(original_bytes)
            
            # gzip压缩
            compressed_bytes = gzip.compress(original_bytes, compresslevel=self.compression_level)
            compressed_size = len(compressed_bytes)
            
            # Base64编码
            compressed_base64 = base64.b64encode(compressed_bytes).decode('ascii')
            
            return compressed_base64, compressed_size, original_size
            
        except Exception as e:
            logger.error(f"FFT数据压缩出错: {e}")
            return "", 0, 0
    
    def should_send_frame(self, current_fft: np.ndarray, 
                         similarity_threshold: float = 0.95,
                         magnitude_threshold_db: float = -80.0) -> bool:
        """判断是否应该发送当前帧"""
        
        # 检查幅度阈值
        max_magnitude = np.max(current_fft)
        if max_magnitude < magnitude_threshold_db:
            return False
        
        # 检查与上一帧的相似度
        if self.last_fft_data is not None:
            try:
                correlation_matrix = np.corrcoef(current_fft, self.last_fft_data)
                similarity = correlation_matrix[0, 1] if correlation_matrix.shape == (2, 2) else 0
                
                if similarity > similarity_threshold:
                    return False  # 太相似，跳过
                    
            except Exception as e:
                logger.debug(f"相似度计算出错: {e}")
                # 计算失败时默认发送
                pass
        
        return True
    
    def get_stats(self) -> dict:
        """获取处理统计信息"""
        avg_processing_time = (
            self.total_processing_time / self.frames_processed 
            if self.frames_processed > 0 else 0
        )
        
        return {
            "frames_processed": self.frames_processed,
            "average_processing_time_ms": avg_processing_time * 1000,
            "buffer_size": len(self.audio_buffer),
            "buffer_ready": self.can_process(),
            "sample_rate": self.sample_rate,
            "fft_size": self.fft_size,
            "frequency_resolution_hz": self.sample_rate / self.fft_size,
            "frequency_range_khz": [0, self.freq_khz[-1]]
        }