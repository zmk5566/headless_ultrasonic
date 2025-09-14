#!/usr/bin/env python3
"""
设备实例管理器
负责管理多个设备实例的生命周期和资源分配
"""
import asyncio
import logging
import time
from typing import Dict, Optional, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor

from .device_instance import DeviceInstance, DeviceState
from .device_manager import DeviceIDManager
from models import StreamConfig, AudioConfig

logger = logging.getLogger(__name__)

class DeviceConflictError(Exception):
    """设备冲突错误"""
    pass

class DeviceInstanceManager:
    """设备实例管理器 - 管理多个并发设备实例"""
    
    def __init__(self, device_id_manager: DeviceIDManager):
        """初始化设备实例管理器
        
        Args:
            device_id_manager: 设备ID管理器
        """
        self.device_id_manager = device_id_manager
        self.device_instances: Dict[str, DeviceInstance] = {}
        self.running_devices: Dict[str, str] = {}  # system_index -> device_id 映射
        
        # 资源管理
        self.max_concurrent_devices = 8  # 最大并发设备数
        self.resource_monitor_task: Optional[asyncio.Task] = None
        
        # 统计信息
        self.total_devices_created = 0
        self.total_devices_started = 0
        self.manager_start_time = time.time()
        
        logger.info("设备实例管理器已初始化")
    
    async def start_monitoring(self):
        """启动资源监控任务"""
        if not self.resource_monitor_task:
            self.resource_monitor_task = asyncio.create_task(self._resource_monitor_loop())
            logger.info("资源监控任务已启动")
    
    async def stop_monitoring(self):
        """停止资源监控任务"""
        if self.resource_monitor_task:
            self.resource_monitor_task.cancel()
            try:
                await self.resource_monitor_task
            except asyncio.CancelledError:
                pass
            self.resource_monitor_task = None
            logger.info("资源监控任务已停止")
    
    def get_available_devices(self) -> List[Dict[str, Any]]:
        """获取可用设备列表"""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            
            # 清理不存在的设备映射
            self.device_id_manager.cleanup_missing_devices(devices)
            
            available_devices = []
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    stable_id, _ = self.device_id_manager.get_or_create_device_id(device, i)
                    
                    # 检查设备状态
                    device_status = "available"
                    instance_state = None
                    
                    if stable_id in self.device_instances:
                        instance = self.device_instances[stable_id]
                        instance_state = instance.state.value
                        
                        if instance.state == DeviceState.RUNNING:
                            device_status = "running"
                        elif instance.state == DeviceState.ERROR:
                            device_status = "error"
                        else:
                            device_status = "stopped"
                    
                    # 检查设备可用性
                    try:
                        sd.check_input_settings(device=i, channels=1, samplerate=device['default_samplerate'])
                    except Exception:
                        if device_status == "available":
                            device_status = "unavailable"
                    
                    available_devices.append({
                        "id": stable_id,
                        "name": device['name'],
                        "system_index": i,
                        "max_channels": device['max_input_channels'],
                        "default_samplerate": device['default_samplerate'],
                        "status": device_status,
                        "instance_state": instance_state,
                        "is_default": i == sd.default.device[0] if hasattr(sd.default, 'device') else False
                    })
            
            return available_devices
            
        except Exception as e:
            logger.error(f"获取可用设备失败: {e}")
            return []
    
    def create_device_instance(
        self, 
        device_id: str, 
        stream_config: StreamConfig,
        audio_config: AudioConfig
    ) -> DeviceInstance:
        """创建设备实例
        
        Args:
            device_id: 稳定设备ID
            stream_config: 流配置
            audio_config: 音频配置
            
        Returns:
            DeviceInstance: 设备实例
            
        Raises:
            DeviceConflictError: 设备已存在
            ValueError: 设备不存在
        """
        if device_id in self.device_instances:
            raise DeviceConflictError(f"设备实例已存在: {device_id}")
        
        # 获取设备信息
        devices_list = []
        try:
            import sounddevice as sd
            devices_list = sd.query_devices()
        except Exception as e:
            raise ValueError(f"无法获取设备列表: {e}")
        
        device_info = self.device_id_manager.get_device_by_stable_id(device_id, devices_list)
        if not device_info:
            raise ValueError(f"设备ID不存在: {device_id}")
        
        device, system_index = device_info
        
        # 创建设备实例
        instance = DeviceInstance(
            device_id=device_id,
            device_name=device['name'],
            system_index=system_index,
            stream_config=stream_config,
            audio_config=audio_config
        )
        
        self.device_instances[device_id] = instance
        self.total_devices_created += 1
        
        logger.info(f"设备实例已创建: {device_id}")
        return instance
    
    async def start_device(self, device_id: str) -> bool:
        """启动设备
        
        Args:
            device_id: 稳定设备ID
            
        Returns:
            bool: 启动是否成功
            
        Raises:
            DeviceConflictError: 设备冲突
            ValueError: 设备不存在
        """
        if device_id not in self.device_instances:
            raise ValueError(f"设备实例不存在: {device_id}")
        
        instance = self.device_instances[device_id]
        
        # 检查资源限制
        running_count = len([d for d in self.device_instances.values() 
                           if d.state == DeviceState.RUNNING])
        
        if running_count >= self.max_concurrent_devices:
            raise DeviceConflictError(f"已达到最大并发设备数限制: {self.max_concurrent_devices}")
        
        # 检查设备冲突
        system_index_str = str(instance.system_index)
        if system_index_str in self.running_devices:
            existing_device_id = self.running_devices[system_index_str]
            if existing_device_id != device_id:
                raise DeviceConflictError(
                    f"设备已被使用: system_index={instance.system_index}, "
                    f"当前使用者: {existing_device_id}"
                )
        
        # 启动设备
        success = await instance.start()
        
        if success:
            self.running_devices[system_index_str] = device_id
            self.total_devices_started += 1
            logger.info(f"设备启动成功: {device_id}")
        else:
            logger.error(f"设备启动失败: {device_id}, 错误: {instance.last_error}")
        
        return success
    
    async def stop_device(self, device_id: str) -> bool:
        """停止设备
        
        Args:
            device_id: 稳定设备ID
            
        Returns:
            bool: 停止是否成功
        """
        if device_id not in self.device_instances:
            return True  # 设备不存在，认为已停止
        
        instance = self.device_instances[device_id]
        success = await instance.stop()
        
        # 清理运行设备映射
        system_index_str = str(instance.system_index)
        if system_index_str in self.running_devices:
            del self.running_devices[system_index_str]
        
        if success:
            logger.info(f"设备停止成功: {device_id}")
        else:
            logger.error(f"设备停止失败: {device_id}, 错误: {instance.last_error}")
        
        return success
    
    async def remove_device_instance(self, device_id: str) -> bool:
        """移除设备实例
        
        Args:
            device_id: 稳定设备ID
            
        Returns:
            bool: 移除是否成功
        """
        if device_id not in self.device_instances:
            return True
        
        # 先停止设备
        await self.stop_device(device_id)
        
        # 移除实例
        del self.device_instances[device_id]
        logger.info(f"设备实例已移除: {device_id}")
        
        return True
    
    def get_device_instance(self, device_id: str) -> Optional[DeviceInstance]:
        """获取设备实例"""
        return self.device_instances.get(device_id)
    
    def get_all_device_instances(self) -> Dict[str, DeviceInstance]:
        """获取所有设备实例"""
        return self.device_instances.copy()
    
    async def stop_all_devices(self):
        """停止所有设备"""
        tasks = []
        for device_id in list(self.device_instances.keys()):
            tasks.append(self.stop_device(device_id))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("所有设备已停止")
    
    async def cleanup_error_devices(self):
        """清理错误状态的设备"""
        error_devices = [
            device_id for device_id, instance in self.device_instances.items()
            if instance.state == DeviceState.ERROR
        ]
        
        for device_id in error_devices:
            await self.remove_device_instance(device_id)
            logger.info(f"已清理错误设备: {device_id}")
    
    async def _resource_monitor_loop(self):
        """资源监控循环"""
        logger.info("资源监控循环已启动")
        
        try:
            while True:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                # 检查设备状态
                error_count = 0
                running_count = 0
                
                for device_id, instance in self.device_instances.items():
                    if instance.state == DeviceState.ERROR:
                        error_count += 1
                        logger.warning(f"检测到错误设备: {device_id}, 错误: {instance.last_error}")
                    elif instance.state == DeviceState.RUNNING:
                        running_count += 1
                
                logger.debug(f"资源监控: 运行中={running_count}, 错误={error_count}, 总计={len(self.device_instances)}")
                
                # 如果错误设备过多，自动清理
                if error_count > 3:
                    logger.info("检测到多个错误设备，执行自动清理")
                    await self.cleanup_error_devices()
                
        except asyncio.CancelledError:
            logger.info("资源监控循环已停止")
        except Exception as e:
            logger.error(f"资源监控循环出错: {e}")
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        running_devices = [d for d in self.device_instances.values() if d.state == DeviceState.RUNNING]
        error_devices = [d for d in self.device_instances.values() if d.state == DeviceState.ERROR]
        
        return {
            "total_instances": len(self.device_instances),
            "running_instances": len(running_devices),
            "error_instances": len(error_devices),
            "max_concurrent_devices": self.max_concurrent_devices,
            "total_devices_created": self.total_devices_created,
            "total_devices_started": self.total_devices_started,
            "uptime_seconds": time.time() - self.manager_start_time,
            "resource_monitor_active": self.resource_monitor_task is not None and not self.resource_monitor_task.done(),
            "running_device_mapping": self.running_devices.copy(),
            "device_states": {
                device_id: instance.state.value 
                for device_id, instance in self.device_instances.items()
            }
        }
    
    async def shutdown(self):
        """关闭管理器"""
        logger.info("设备实例管理器正在关闭...")
        
        # 停止资源监控
        await self.stop_monitoring()
        
        # 停止所有设备
        await self.stop_all_devices()
        
        # 清理所有实例
        self.device_instances.clear()
        self.running_devices.clear()
        
        logger.info("设备实例管理器已关闭")