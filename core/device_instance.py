#!/usr/bin/env python3
"""
设备实例模块
封装单个音频设备的完整处理链路
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any, Callable
from enum import Enum

from .audio_capture import AudioCapture
from .fft_processor import FFTProcessor
from .data_streamer import DataStreamer
from models import StreamConfig, AudioConfig, FFTFrame

logger = logging.getLogger(__name__)

class DeviceState(Enum):
    """设备状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

class DeviceInstance:
    """设备实例类 - 封装单个设备的完整音频处理链"""
    
    def __init__(
        self, 
        device_id: str,
        device_name: str,
        system_index: int,
        stream_config: StreamConfig,
        audio_config: AudioConfig
    ):
        """初始化设备实例
        
        Args:
            device_id: 稳定设备ID
            device_name: 设备名称
            system_index: 系统设备索引
            stream_config: 流配置
            audio_config: 音频配置
        """
        self.device_id = device_id
        self.device_name = device_name
        self.system_index = system_index
        self.stream_config = stream_config.copy()
        self.audio_config = audio_config.copy()
        
        # 状态管理
        self.state = DeviceState.STOPPED
        self.last_error = None
        self.start_time = None
        
        # 组件实例
        self.audio_capture: Optional[AudioCapture] = None
        self.fft_processor: Optional[FFTProcessor] = None
        self.data_streamer: Optional[DataStreamer] = None
        
        # 处理任务
        self.processing_task: Optional[asyncio.Task] = None
        self.sequence_id = 0
        
        # 统计信息
        self.stats = {
            "frames_processed": 0,
            "frames_sent": 0,
            "errors_count": 0,
            "uptime_seconds": 0.0,
            "current_fps": 0.0
        }
        
        logger.info(f"设备实例已创建: {device_id} ({device_name})")
    
    async def initialize(self) -> bool:
        """初始化设备组件"""
        try:
            self.state = DeviceState.STARTING
            
            # 创建FFT处理器
            self.fft_processor = FFTProcessor(
                sample_rate=self.audio_config.sample_rate,
                fft_size=self.audio_config.fft_size,
                overlap=self.audio_config.overlap,
                window_type=self.audio_config.window_type,
                compression_level=self.stream_config.compression_level,
                threshold_db=self.audio_config.threshold_db
            )
            
            # 创建数据流管理器
            self.data_streamer = DataStreamer(self.stream_config)
            
            # 创建音频采集器（指定特定设备）
            self.audio_capture = AudioCapture(
                device_names=[self.device_name],  # 只使用当前设备
                fallback_device_id=self.system_index,
                sample_rate=self.audio_config.sample_rate,
                channels=self.audio_config.channels,
                blocksize=self.audio_config.blocksize
            )
            
            # 设置音频回调
            self.audio_capture.add_callback(self._audio_callback)
            
            logger.info(f"设备组件初始化完成: {self.device_id}")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            self.state = DeviceState.ERROR
            logger.error(f"设备初始化失败 {self.device_id}: {e}")
            return False
    
    async def start(self) -> bool:
        """启动设备"""
        if self.state == DeviceState.RUNNING:
            return True
            
        try:
            self.state = DeviceState.STARTING
            
            # 如果组件未初始化，先初始化
            if not self.audio_capture:
                if not await self.initialize():
                    return False
            
            # 启动音频采集
            success = self.audio_capture.start()
            if not success:
                self.state = DeviceState.ERROR
                self.last_error = "音频采集启动失败"
                return False
            
            # 启动数据处理循环
            self.processing_task = asyncio.create_task(self._data_processing_loop())
            
            self.state = DeviceState.RUNNING
            self.start_time = time.time()
            logger.info(f"设备已启动: {self.device_id}")
            
            return True
            
        except Exception as e:
            self.last_error = str(e)
            self.state = DeviceState.ERROR
            logger.error(f"启动设备失败 {self.device_id}: {e}")
            return False
    
    async def stop(self) -> bool:
        """停止设备"""
        if self.state == DeviceState.STOPPED:
            return True
            
        try:
            self.state = DeviceState.STOPPING
            
            # 停止音频采集
            if self.audio_capture:
                self.audio_capture.stop()
            
            # 取消处理任务
            if self.processing_task and not self.processing_task.done():
                self.processing_task.cancel()
                try:
                    await self.processing_task
                except asyncio.CancelledError:
                    pass
            
            self.state = DeviceState.STOPPED
            logger.info(f"设备已停止: {self.device_id}")
            
            return True
            
        except Exception as e:
            self.last_error = str(e)
            self.state = DeviceState.ERROR
            logger.error(f"停止设备失败 {self.device_id}: {e}")
            return False
    
    def _audio_callback(self, audio_data, timestamp):
        """音频数据回调"""
        if self.fft_processor and self.state == DeviceState.RUNNING:
            logger.debug(f"设备 {self.device_id} 音频回调: 数据长度={len(audio_data)}")
            self.fft_processor.add_audio_data(audio_data)
    
    async def _data_processing_loop(self):
        """数据处理循环"""
        logger.info(f"设备 {self.device_id} 数据处理循环已启动")
        
        try:
            loop_count = 0
            while self.state == DeviceState.RUNNING:
                loop_count += 1
                
                # 每1000次循环输出一次调试信息
                if loop_count % 1000 == 0:
                    buffer_stats = self.fft_processor.get_stats()
                    client_count = len(self.data_streamer.clients) if self.data_streamer else 0
                    logger.debug(f"设备 {self.device_id} 处理循环 #{loop_count}: 缓冲区大小={buffer_stats.get('buffer_size', 0)}, 客户端数={client_count}")
                
                # 检查是否需要发送新帧
                current_time = time.time()
                should_send_time = self.data_streamer.should_send_frame(current_time)
                
                if not should_send_time:
                    await asyncio.sleep(0.001)
                    continue
                
                # 检查是否有足够数据处理FFT
                can_process = self.fft_processor.can_process()
                if not can_process:
                    await asyncio.sleep(0.001)
                    continue
                
                # 添加调试日志表示开始FFT处理
                logger.debug(f"设备 {self.device_id} 开始FFT处理 (帧 #{self.sequence_id + 1})")
                
                # 处理FFT
                result = self.fft_processor.process_fft()
                if result is None:
                    logger.debug(f"设备 {self.device_id} FFT处理返回None")
                    continue
                
                magnitude_db, metadata = result
                self.stats["frames_processed"] += 1
                logger.debug(f"设备 {self.device_id} FFT处理成功，峰值频率={metadata['peak_frequency_hz']/1000:.1f}kHz")
                
                # 智能跳帧检查（可配置关闭）
                should_send_smart = True
                if self.stream_config.enable_smart_skip:
                    should_send_smart = self.fft_processor.should_send_frame(
                        magnitude_db,
                        self.stream_config.similarity_threshold,
                        self.stream_config.magnitude_threshold_db
                    )
                
                if not should_send_smart:
                    logger.debug(f"设备 {self.device_id} 智能跳帧检查：跳过帧")
                    continue
                
                # 压缩数据
                compressed_data, compressed_size, original_size = \
                    self.fft_processor.compress_fft_data(magnitude_db)
                if not compressed_data:
                    logger.debug(f"设备 {self.device_id} 数据压缩失败")
                    continue
                
                logger.debug(f"设备 {self.device_id} 数据压缩成功，原始={original_size}字节，压缩后={compressed_size}字节")
                
                # 创建FFT帧
                self.sequence_id += 1
                fft_frame = FFTFrame(
                    timestamp=current_time * 1000,
                    sequence_id=self.sequence_id,
                    sample_rate=self.audio_config.sample_rate,
                    fft_size=self.audio_config.fft_size,
                    data_compressed=compressed_data,
                    compression_method="gzip",
                    data_size_bytes=compressed_size,
                    original_size_bytes=original_size,
                    peak_frequency_hz=metadata["peak_frequency_hz"],
                    peak_magnitude_db=metadata["peak_magnitude_db"],
                    spl_db=metadata["spl_db"],
                    fps=0.0  # 将在data_streamer中更新
                )
                
                # 广播到客户端
                logger.debug(f"设备 {self.device_id} 准备广播帧 #{self.sequence_id}")
                await self.data_streamer.broadcast_frame(fft_frame, current_time)
                self.stats["frames_sent"] += 1
                logger.debug(f"设备 {self.device_id} 帧 #{self.sequence_id} 广播完成")
                
                # 小延迟避免CPU过载
                await asyncio.sleep(0.001)
                
        except asyncio.CancelledError:
            logger.info(f"设备 {self.device_id} 数据处理循环已停止")
        except Exception as e:
            self.last_error = str(e)
            self.stats["errors_count"] += 1
            logger.error(f"设备 {self.device_id} 数据处理循环出错: {e}")
            self.state = DeviceState.ERROR
    
    def get_status(self) -> Dict[str, Any]:
        """获取设备状态"""
        # 更新运行时间
        if self.start_time:
            self.stats["uptime_seconds"] = time.time() - self.start_time
        
        # 获取组件统计
        audio_stats = self.audio_capture.get_stats() if self.audio_capture else {}
        fft_stats = self.fft_processor.get_stats() if self.fft_processor else {}
        stream_stats = self.data_streamer.get_stats() if self.data_streamer else {}
        
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "system_index": self.system_index,
            "state": self.state.value,
            "last_error": self.last_error,
            "stats": self.stats,
            "audio_stats": audio_stats,
            "fft_stats": fft_stats,
            "stream_stats": stream_stats,
            "config": {
                "stream": self.stream_config.dict(),
                "audio": self.audio_config.dict()
            }
        }
    
    def update_stream_config(self, new_config: StreamConfig):
        """更新流配置"""
        self.stream_config = new_config.copy()
        if self.data_streamer:
            self.data_streamer.update_config(new_config)
        logger.info(f"设备 {self.device_id} 流配置已更新")
    
    def update_audio_config(self, new_config: AudioConfig):
        """更新音频配置（需要重启设备）"""
        self.audio_config = new_config.copy()
        logger.info(f"设备 {self.device_id} 音频配置已更新（需重启生效）")
    
    async def get_stream_generator(self, request):
        """获取SSE流生成器"""
        if not self.data_streamer:
            raise RuntimeError(f"设备 {self.device_id} 数据流未初始化")
        
        return await self.data_streamer.create_client_stream(request)
    
    def __del__(self):
        """析构函数"""
        if self.processing_task and not self.processing_task.done():
            self.processing_task.cancel()