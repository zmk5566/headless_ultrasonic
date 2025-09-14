#!/usr/bin/env python3
"""
JSON 配置加载器
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    # 确定配置文件路径
    if getattr(sys, 'frozen', False):
        # PyInstaller 编译后
        app_path = os.path.dirname(sys.executable)
        config_path = os.path.join(app_path, '_internal', 'config.json')
        if not os.path.exists(config_path):
            config_path = os.path.join(app_path, 'config.json')
    else:
        # 正常 Python 环境
        app_path = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(app_path, 'config.json')
    
    # 加载配置
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"配置加载成功: {config_path}")
        return config
    except FileNotFoundError:
        print(f"警告: 配置文件不存在 {config_path}，使用默认配置")
        return get_default_config()
    except json.JSONDecodeError as e:
        print(f"警告: 配置文件格式错误 {e}，使用默认配置")
        return get_default_config()

def get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return {
        "server": {
            "host": "0.0.0.0",
            "port": 8380,
            "debug": False
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "data": {
            "data_dir": "./data"
        },
        "stream": {
            "target_fps": 30,
            "compression_level": 6,
            "enable_adaptive_fps": True,
            "min_fps": 5,
            "max_fps": 60,
            "magnitude_threshold_db": -80.0,
            "enable_smart_skip": False,
            "similarity_threshold": 0.95
        },
        "audio": {
            "device_names": ["UltraMic384K", "UltraMic", "384K"],
            "fallback_device_id": None,
            "sample_rate": 384000,
            "channels": 1,
            "blocksize": 3840,
            "fft_size": 8192,
            "overlap": 0.75,
            "window_type": "hann",
            "threshold_db": -100.0
        }
    }

# 全局配置对象
_config = None

def get_config() -> Dict[str, Any]:
    """获取配置（单例模式）"""
    global _config
    if _config is None:
        _config = load_config()
    return _config

class Config:
    """兼容旧代码的配置类"""
    
    def __init__(self):
        self._cfg = get_config()
    
    @property
    def HOST(self):
        return os.getenv("HOST", self._cfg["server"]["host"])
    
    @property
    def PORT(self):
        return int(os.getenv("PORT", str(self._cfg["server"]["port"])))
    
    @property
    def DEBUG(self):
        debug_env = os.getenv("DEBUG")
        if debug_env:
            return debug_env.lower() == "true"
        return self._cfg["server"]["debug"]
    
    @property
    def LOG_LEVEL(self):
        return os.getenv("LOG_LEVEL", self._cfg["logging"]["level"])
    
    @property
    def LOG_FORMAT(self):
        return self._cfg["logging"]["format"]
    
    @property
    def DATA_DIR(self):
        return Path(os.getenv("DATA_DIR", self._cfg["data"]["data_dir"]))
    
    def get_stream_config(self):
        """获取流配置"""
        from models import StreamConfig
        cfg = self._cfg["stream"]
        return StreamConfig(
            target_fps=int(os.getenv("TARGET_FPS", str(cfg["target_fps"]))),
            compression_level=int(os.getenv("COMPRESSION_LEVEL", str(cfg["compression_level"]))),
            enable_adaptive_fps=cfg["enable_adaptive_fps"],
            min_fps=cfg["min_fps"],
            max_fps=cfg["max_fps"],
            magnitude_threshold_db=cfg["magnitude_threshold_db"],
            enable_smart_skip=cfg["enable_smart_skip"],
            similarity_threshold=cfg["similarity_threshold"]
        )
    
    def get_audio_config(self):
        """获取音频配置"""
        from models import AudioConfig
        cfg = self._cfg["audio"]
        device_names = os.getenv("DEVICE_NAMES")
        if device_names:
            device_names = device_names.split(",")
        else:
            device_names = cfg["device_names"]
            
        return AudioConfig(
            device_names=device_names,
            fallback_device_id=cfg["fallback_device_id"],
            sample_rate=int(os.getenv("SAMPLE_RATE", str(cfg["sample_rate"]))),
            channels=cfg["channels"],
            blocksize=cfg["blocksize"],
            fft_size=cfg["fft_size"],
            overlap=cfg["overlap"],
            window_type=cfg["window_type"],
            threshold_db=cfg["threshold_db"]
        )

# 创建全局配置实例
Config = Config()