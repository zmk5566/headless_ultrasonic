#!/usr/bin/env python3
"""
动态配置控制API端点
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/config", tags=["configuration"])

# 全局组件引用 (将在main.py中设置)
components = {}

def set_config_components(audio_capture, fft_processor, data_streamer, stream_config, audio_config):
    """设置全局组件引用"""
    global components
    components = {
        'audio_capture': audio_capture,
        'fft_processor': fft_processor, 
        'data_streamer': data_streamer,
        'stream_config': stream_config,
        'audio_config': audio_config
    }

# ============================================================================
# 数据模型
# ============================================================================

class FPSConfig(BaseModel):
    """FPS配置"""
    target_fps: int = Field(ge=1, le=120, description="目标帧率 (1-120)")

class ThresholdConfig(BaseModel):
    """阈值配置"""
    threshold_db: float = Field(ge=-200, le=0, description="dB阈值 (-200 到 0)")
    magnitude_threshold_db: float = Field(ge=-200, le=0, description="幅度阈值 (-200 到 0)")
    similarity_threshold: float = Field(ge=0.0, le=1.0, description="相似度阈值 (0.0 到 1.0)")

class CompressionConfig(BaseModel):
    """压缩配置"""
    compression_level: int = Field(ge=1, le=9, description="压缩级别 (1-9)")

class FilterConfig(BaseModel):
    """过滤配置"""
    enable_smart_skip: bool = Field(description="启用智能跳帧")
    enable_adaptive_fps: bool = Field(description="启用自适应FPS")

class ConfigResponse(BaseModel):
    """配置响应"""
    success: bool
    message: str
    current_config: dict

# ============================================================================
# 热更新API (不需要重启)
# ============================================================================

@router.post("/fps")
async def update_fps(config: FPSConfig):
    """动态更新目标FPS"""
    try:
        if 'stream_config' not in components:
            raise HTTPException(status_code=503, detail="组件未初始化")
        
        old_fps = components['stream_config'].target_fps
        components['stream_config'].target_fps = config.target_fps
        
        # 同时更新data_streamer的内部配置（如果支持）
        if 'data_streamer' in components:
            if hasattr(components['data_streamer'], 'update_config'):
                components['data_streamer'].update_config(components['stream_config'])
        
        logger.info(f"FPS已更新: {old_fps} -> {config.target_fps}")
        
        return ConfigResponse(
            success=True,
            message=f"FPS已更新为 {config.target_fps}",
            current_config={"target_fps": config.target_fps}
        )
        
    except Exception as e:
        logger.error(f"更新FPS失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新FPS失败: {str(e)}")

@router.post("/threshold")  
async def update_threshold(config: ThresholdConfig):
    """动态更新各种阈值"""
    try:
        if 'fft_processor' not in components or 'stream_config' not in components:
            raise HTTPException(status_code=503, detail="组件未初始化")
            
        old_config = {
            'threshold_db': components['fft_processor'].threshold_db,
            'magnitude_threshold_db': components['stream_config'].magnitude_threshold_db,
            'similarity_threshold': components['stream_config'].similarity_threshold
        }
        
        # 更新FFT处理器阈值
        components['fft_processor'].threshold_db = config.threshold_db
        
        # 更新流配置阈值
        components['stream_config'].magnitude_threshold_db = config.magnitude_threshold_db
        components['stream_config'].similarity_threshold = config.similarity_threshold
        
        # 同步到data_streamer（如果支持）
        if 'data_streamer' in components:
            if hasattr(components['data_streamer'], 'update_config'):
                components['data_streamer'].update_config(components['stream_config'])
        
        logger.info(f"阈值已更新: {old_config} -> {config.dict()}")
        
        return ConfigResponse(
            success=True,
            message="所有阈值已更新",
            current_config=config.dict()
        )
        
    except Exception as e:
        logger.error(f"更新阈值失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新阈值失败: {str(e)}")

@router.post("/compression")
async def update_compression(config: CompressionConfig):
    """动态更新压缩配置"""
    try:
        if 'fft_processor' not in components or 'stream_config' not in components:
            raise HTTPException(status_code=503, detail="组件未初始化")
            
        old_level = components['fft_processor'].compression_level
        components['fft_processor'].compression_level = config.compression_level
        components['stream_config'].compression_level = config.compression_level
        
        logger.info(f"压缩级别已更新: {old_level} -> {config.compression_level}")
        
        return ConfigResponse(
            success=True,
            message=f"压缩级别已更新为 {config.compression_level}",
            current_config={"compression_level": config.compression_level}
        )
        
    except Exception as e:
        logger.error(f"更新压缩配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新压缩配置失败: {str(e)}")

@router.post("/filter")
async def update_filter(config: FilterConfig):
    """动态更新过滤配置"""
    try:
        if 'stream_config' not in components:
            raise HTTPException(status_code=503, detail="组件未初始化")
            
        old_config = {
            'enable_smart_skip': components['stream_config'].enable_smart_skip,
            'enable_adaptive_fps': components['stream_config'].enable_adaptive_fps
        }
        
        components['stream_config'].enable_smart_skip = config.enable_smart_skip
        components['stream_config'].enable_adaptive_fps = config.enable_adaptive_fps
        
        # 同步到data_streamer（如果支持）
        if 'data_streamer' in components:
            if hasattr(components['data_streamer'], 'update_config'):
                components['data_streamer'].update_config(components['stream_config'])
        
        logger.info(f"过滤配置已更新: {old_config} -> {config.dict()}")
        
        return ConfigResponse(
            success=True,
            message="过滤配置已更新",
            current_config=config.dict()
        )
        
    except Exception as e:
        logger.error(f"更新过滤配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新过滤配置失败: {str(e)}")

# ============================================================================
# 配置查询API
# ============================================================================

@router.get("/current")
async def get_current_config():
    """获取当前所有配置"""
    try:
        if not components:
            raise HTTPException(status_code=503, detail="组件未初始化")
            
        config = {
            "stream_config": {
                "target_fps": components['stream_config'].target_fps,
                "compression_level": components['stream_config'].compression_level,
                "enable_adaptive_fps": components['stream_config'].enable_adaptive_fps,
                "enable_smart_skip": components['stream_config'].enable_smart_skip,
                "magnitude_threshold_db": components['stream_config'].magnitude_threshold_db,
                "similarity_threshold": components['stream_config'].similarity_threshold,
                "min_fps": components['stream_config'].min_fps,
                "max_fps": components['stream_config'].max_fps
            },
            "audio_config": {
                "sample_rate": components['audio_config'].sample_rate,
                "fft_size": components['audio_config'].fft_size,
                "overlap": components['audio_config'].overlap,
                "window_type": components['audio_config'].window_type,
                "threshold_db": components['audio_config'].threshold_db,
                "channels": components['audio_config'].channels,
                "blocksize": components['audio_config'].blocksize
            },
            "fft_processor": {
                "threshold_db": components['fft_processor'].threshold_db,
                "compression_level": components['fft_processor'].compression_level,
                "frames_processed": components['fft_processor'].frames_processed
            }
        }
        
        return ConfigResponse(
            success=True,
            message="当前配置获取成功",
            current_config=config
        )
        
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@router.get("/presets")
async def get_config_presets():
    """获取配置预设"""
    presets = {
        "low_noise": {
            "name": "低噪声模式",
            "description": "适合安静环境，高灵敏度",
            "threshold_db": -120.0,
            "magnitude_threshold_db": -90.0,
            "similarity_threshold": 0.90,
            "target_fps": 30,
            "compression_level": 9
        },
        "balanced": {
            "name": "平衡模式",
            "description": "默认推荐设置",
            "threshold_db": -100.0,
            "magnitude_threshold_db": -80.0,
            "similarity_threshold": 0.95,
            "target_fps": 30,
            "compression_level": 6
        },
        "high_signal": {
            "name": "强信号模式", 
            "description": "只显示强信号，适合嘈杂环境",
            "threshold_db": -80.0,
            "magnitude_threshold_db": -60.0,
            "similarity_threshold": 0.98,
            "target_fps": 60,
            "compression_level": 3
        },
        "performance": {
            "name": "性能优先",
            "description": "最低CPU占用，适合长时间监控",
            "threshold_db": -90.0,
            "magnitude_threshold_db": -70.0,
            "similarity_threshold": 0.99,
            "target_fps": 15,
            "compression_level": 9
        }
    }
    
    return {"presets": presets}

@router.post("/apply_preset/{preset_name}")
async def apply_preset(preset_name: str):
    """应用配置预设"""
    presets = await get_config_presets()
    
    if preset_name not in presets["presets"]:
        raise HTTPException(status_code=404, detail="预设不存在")
        
    preset = presets["presets"][preset_name]
    
    try:
        # 应用FPS配置
        await update_fps(FPSConfig(target_fps=preset["target_fps"]))
        
        # 应用阈值配置
        await update_threshold(ThresholdConfig(
            threshold_db=preset["threshold_db"],
            magnitude_threshold_db=preset["magnitude_threshold_db"], 
            similarity_threshold=preset["similarity_threshold"]
        ))
        
        # 应用压缩配置
        await update_compression(CompressionConfig(
            compression_level=preset["compression_level"]
        ))
        
        logger.info(f"已应用预设: {preset_name}")
        
        return ConfigResponse(
            success=True,
            message=f"已应用预设: {preset['name']}",
            current_config=preset
        )
        
    except Exception as e:
        logger.error(f"应用预设失败: {e}")
        raise HTTPException(status_code=500, detail=f"应用预设失败: {str(e)}")