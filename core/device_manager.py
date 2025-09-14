#!/usr/bin/env python3
"""
设备ID管理器
提供稳定的设备标识符映射和持久化存储
"""
import json
import hashlib
import logging
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class DeviceIDManager:
    """设备ID管理器，负责生成和维护稳定的设备标识符"""
    
    def __init__(self, config_dir: str = None):
        """初始化设备ID管理器
        
        Args:
            config_dir: 配置文件目录，默认为当前目录
        """
        if config_dir is None:
            config_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "device_mapping.json"
        self.device_mapping = {}  # stable_id -> device_signature
        self.reverse_mapping = {}  # device_signature -> stable_id
        self.load_mapping()
        
    def generate_device_signature(self, device: dict, system_index: int) -> str:
        """生成设备签名，用于识别同一设备
        
        Args:
            device: sounddevice设备信息
            system_index: 系统索引（作为备用标识）
            
        Returns:
            设备签名字符串
        """
        # 提取关键设备信息
        key_info = {
            "name": device.get('name', ''),
            "hostapi": device.get('hostapi', 0),
            "max_input_channels": device.get('max_input_channels', 0),
            "max_output_channels": device.get('max_output_channels', 0),
            "default_samplerate": device.get('default_samplerate', 0)
        }
        
        # 创建设备签名
        signature_string = f"{key_info['name']}|{key_info['hostapi']}|{key_info['max_input_channels']}|{key_info['default_samplerate']}"
        
        # 生成哈希
        signature_hash = hashlib.sha256(signature_string.encode()).hexdigest()[:12]
        
        return f"sig_{signature_hash}"
    
    def generate_stable_id(self, device_signature: str, device_name: str) -> str:
        """为设备签名生成稳定ID
        
        Args:
            device_signature: 设备签名
            device_name: 设备名称
            
        Returns:
            稳定的设备ID
        """
        # 清理设备名称，生成友好的ID前缀
        clean_name = "".join(c for c in device_name if c.isalnum() or c in "-_").lower()
        clean_name = clean_name[:16]  # 限制长度
        
        # 基础ID
        base_id = f"{clean_name}_{device_signature[-6:]}"
        
        # 检查是否已存在，如果存在则添加序号
        counter = 1
        stable_id = base_id
        while stable_id in self.device_mapping and self.device_mapping[stable_id] != device_signature:
            stable_id = f"{base_id}_{counter}"
            counter += 1
            
        return stable_id
    
    def get_or_create_device_id(self, device: dict, system_index: int) -> Tuple[str, int]:
        """获取或创建设备的稳定ID
        
        Args:
            device: sounddevice设备信息
            system_index: 系统索引
            
        Returns:
            (stable_device_id, system_index)
        """
        device_signature = self.generate_device_signature(device, system_index)
        
        # 检查是否已有映射
        if device_signature in self.reverse_mapping:
            stable_id = self.reverse_mapping[device_signature]
            logger.debug(f"找到现有设备映射: {device['name']} -> {stable_id}")
        else:
            # 创建新映射
            stable_id = self.generate_stable_id(device_signature, device['name'])
            self.device_mapping[stable_id] = device_signature
            self.reverse_mapping[device_signature] = stable_id
            logger.info(f"创建新设备映射: {device['name']} -> {stable_id}")
            
            # 保存映射
            self.save_mapping()
            
        return stable_id, system_index
    
    def get_device_by_stable_id(self, stable_id: str, devices_list: List[dict]) -> Optional[Tuple[dict, int]]:
        """通过稳定ID找到对应的设备
        
        Args:
            stable_id: 稳定设备ID
            devices_list: 当前系统设备列表
            
        Returns:
            (device, system_index) 或 None
        """
        if stable_id not in self.device_mapping:
            return None
            
        target_signature = self.device_mapping[stable_id]
        
        # 在当前设备列表中查找匹配的设备
        for i, device in enumerate(devices_list):
            device_signature = self.generate_device_signature(device, i)
            if device_signature == target_signature:
                return device, i
                
        logger.warning(f"无法找到稳定ID对应的设备: {stable_id}")
        return None
    
    def load_mapping(self):
        """从文件加载设备映射"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.device_mapping = data.get('device_mapping', {})
                self.reverse_mapping = data.get('reverse_mapping', {})
                
                # 验证映射完整性
                if len(self.device_mapping) != len(self.reverse_mapping):
                    logger.warning("设备映射文件不一致，重建反向映射")
                    self.rebuild_reverse_mapping()
                    
                logger.info(f"加载了 {len(self.device_mapping)} 个设备映射")
            else:
                logger.info("设备映射文件不存在，将创建新文件")
                
        except Exception as e:
            logger.error(f"加载设备映射失败: {e}")
            self.device_mapping = {}
            self.reverse_mapping = {}
    
    def save_mapping(self):
        """保存设备映射到文件"""
        try:
            # 确保目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            data = {
                'device_mapping': self.device_mapping,
                'reverse_mapping': self.reverse_mapping,
                'version': '1.0',
                'description': 'Audio device stable ID mapping for headless_ultrasonic'
            }
            
            # 原子写入
            temp_file = self.config_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            temp_file.replace(self.config_file)
            logger.debug(f"设备映射已保存到: {self.config_file}")
            
        except Exception as e:
            logger.error(f"保存设备映射失败: {e}")
    
    def rebuild_reverse_mapping(self):
        """重建反向映射"""
        self.reverse_mapping = {v: k for k, v in self.device_mapping.items()}
        self.save_mapping()
    
    def cleanup_missing_devices(self, current_devices: List[dict]):
        """清理不再存在的设备映射
        
        Args:
            current_devices: 当前系统设备列表
        """
        current_signatures = set()
        for i, device in enumerate(current_devices):
            signature = self.generate_device_signature(device, i)
            current_signatures.add(signature)
            
        # 找出不再存在的设备
        missing_signatures = set(self.reverse_mapping.keys()) - current_signatures
        
        if missing_signatures:
            logger.info(f"清理 {len(missing_signatures)} 个丢失的设备映射")
            
            for signature in missing_signatures:
                if signature in self.reverse_mapping:
                    stable_id = self.reverse_mapping[signature]
                    del self.reverse_mapping[signature]
                    if stable_id in self.device_mapping:
                        del self.device_mapping[stable_id]
                        
            if missing_signatures:
                self.save_mapping()
    
    def get_mapping_stats(self) -> Dict:
        """获取映射统计信息"""
        return {
            "total_mappings": len(self.device_mapping),
            "config_file": str(self.config_file),
            "file_exists": self.config_file.exists(),
            "file_size_bytes": self.config_file.stat().st_size if self.config_file.exists() else 0
        }
    
    def export_mapping(self) -> Dict:
        """导出完整映射信息（用于调试）"""
        return {
            "device_mapping": self.device_mapping,
            "reverse_mapping": self.reverse_mapping,
            "stats": self.get_mapping_stats()
        }