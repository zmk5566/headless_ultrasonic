#!/usr/bin/env python3
"""
音频数据采集模块
从fast_ultrasonic.py的AudioThread改进而来，增加更好的错误处理和状态管理
"""
import sounddevice as sd
import numpy as np
from threading import Thread, Event
from collections import deque
from typing import Optional, Callable, List
import logging
import time

logger = logging.getLogger(__name__)

class AudioCapture:
    """高性能音频采集类"""
    
    def __init__(self, 
                 device_names: List[str] = None,
                 fallback_device_id: Optional[int] = None,
                 sample_rate: int = 384000,
                 channels: int = 1,
                 blocksize: int = 3840,
                 dtype=np.int16):
        
        self.device_names = device_names or ["UltraMic384K", "UltraMic", "384K"]
        self.fallback_device_id = fallback_device_id
        self.sample_rate = sample_rate
        self.channels = channels
        self.blocksize = blocksize
        self.dtype = dtype
        
        self.device = None
        self.device_name = None
        self.is_running = False
        self._stop_event = Event()
        self._capture_thread = None
        self._callbacks = []
        
        # 性能统计
        self.frames_captured = 0
        self.bytes_captured = 0
        self.start_time = None
        self.last_error = None
        
        # 设备断开检测
        self.last_callback_time = 0
        self.callback_timeout = 10.0  # 10秒没有回调认为设备断开 (为MacBook Air麦克风增加容忍度)
        self.device_disconnected = False
        
    def add_callback(self, callback: Callable[[np.ndarray, float], None]):
        """添加音频数据回调函数
        
        Args:
            callback: 回调函数，接收(audio_data: np.ndarray, timestamp: float)
        """
        self._callbacks.append(callback)
        
    def remove_callback(self, callback: Callable):
        """移除回调函数"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def find_device(self) -> Optional[int]:
        """查找音频设备"""
        try:
            devices = sd.query_devices()
            
            # 首先尝试通过名字匹配
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    for name in self.device_names:
                        if name in device['name']:
                            logger.info(f"找到设备: {i} - {device['name']} (通过名字 '{name}')")
                            self.device_name = device['name']
                            return i
            
            # 尝试回退设备
            if (self.fallback_device_id is not None and 
                self.fallback_device_id < len(devices)):
                device = devices[self.fallback_device_id]
                if device['max_input_channels'] > 0:
                    logger.info(f"使用回退设备: {self.fallback_device_id} - {device['name']}")
                    self.device_name = device['name']
                    return self.fallback_device_id
            
            # 使用默认输入设备
            try:
                default_device = sd.query_devices(kind='input')
                logger.info(f"使用默认输入设备: {default_device['name']}")
                self.device_name = default_device['name']
                return None  # None表示默认设备
            except Exception as e:
                logger.error(f"无法获取默认设备: {e}")
                
        except Exception as e:
            logger.error(f"查找设备时发生错误: {e}")
            
        # 列出所有可用设备供调试
        logger.info("可用输入设备:")
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    logger.info(f"  {i}: {device['name']}")
        except Exception as e:
            logger.error(f"无法列出设备: {e}")
            
        return None
    
    def start(self) -> bool:
        """启动音频采集"""
        if self.is_running:
            logger.warning("音频采集已在运行中")
            return True
            
        try:
            self.device = self.find_device()
            if self.device is None and not self.device_name:
                self.last_error = "未找到可用的音频设备"
                logger.error(self.last_error)
                return False
                
            self._stop_event.clear()
            self._capture_thread = Thread(target=self._capture_loop, daemon=True)
            self._capture_thread.start()
            
            self.is_running = True
            self.start_time = time.time()
            self.frames_captured = 0
            self.bytes_captured = 0
            
            logger.info(f"音频采集已启动: {self.device_name}")
            logger.info(f"采样率: {self.sample_rate} Hz, 块大小: {self.blocksize}")
            return True
            
        except Exception as e:
            self.last_error = f"启动音频采集失败: {e}"
            logger.error(self.last_error)
            return False
    
    def stop(self):
        """停止音频采集"""
        if not self.is_running:
            return
            
        logger.info("正在停止音频采集...")
        self.is_running = False
        self._stop_event.set()
        
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=2.0)
            
        logger.info("音频采集已停止")
    
    def _capture_loop(self):
        """音频采集主循环"""
        def audio_callback(indata, frames, time_info, status):
            if not self.is_running:
                return
                
            if status:
                logger.warning(f"音频回调状态: {status}")
                # 检查是否是设备断开错误
                if 'input underflow' in str(status).lower() or 'device' in str(status).lower():
                    logger.error(f"疑似设备断开: {status}")
                    self.device_disconnected = True
                    return
                
            try:
                # 转换为float并归一化
                audio_float = indata.flatten().astype(np.float32) / 32768.0
                
                # 记录统计信息
                self.frames_captured += 1
                self.bytes_captured += len(audio_float) * 4  # float32 = 4 bytes
                self.last_callback_time = time.time()  # 更新最后回调时间
                self.device_disconnected = False  # 收到数据说明设备正常
                
                # 调用所有回调函数，传入时间戳
                timestamp = time.time() * 1000  # 毫秒时间戳
                for callback in self._callbacks:
                    try:
                        callback(audio_float, timestamp)
                    except Exception as e:
                        logger.error(f"音频回调函数出错: {e}")
                        
            except Exception as e:
                logger.error(f"音频数据处理出错: {e}")
        
        try:
            with sd.InputStream(
                device=self.device,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=self.dtype,
                blocksize=self.blocksize,
                callback=audio_callback
            ):
                logger.info("音频流已打开，开始采集数据...")
                self.last_callback_time = time.time()
                while not self._stop_event.wait(0.1):  # 100ms检查间隔
                    # 检查设备是否长时间无响应
                    if time.time() - self.last_callback_time > self.callback_timeout:
                        self.device_disconnected = True
                        self.last_error = "设备长时间无响应，可能已断开"
                        logger.error(self.last_error)
                        break
                    
                    # 检查设备断开标志
                    if self.device_disconnected:
                        self.last_error = "音频设备已断开"
                        logger.error(self.last_error)
                        break
                    
        except Exception as e:
            self.last_error = f"音频流错误: {e}"
            logger.error(self.last_error)
            self.is_running = False
    
    def get_stats(self) -> dict:
        """获取采集统计信息"""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            "is_running": self.is_running,
            "device_name": self.device_name,
            "frames_captured": self.frames_captured,
            "bytes_captured": self.bytes_captured,
            "uptime_seconds": uptime,
            "fps": self.frames_captured / uptime if uptime > 0 else 0,
            "last_error": self.last_error,
            "device_disconnected": self.device_disconnected,
            "last_callback_time": self.last_callback_time,
            "callback_health": "healthy" if time.time() - self.last_callback_time < self.callback_timeout else "timeout"
        }
    
    def __del__(self):
        """析构时确保停止采集"""
        self.stop()