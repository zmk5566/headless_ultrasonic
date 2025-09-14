#!/usr/bin/env python3
"""
每设备控制API端点
提供单设备的启停、配置和状态管理
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import logging

from models import StreamConfig, AudioConfig, ControlResponse
from core import DeviceInstanceManager, DeviceConflictError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/devices", tags=["device-control"])

# 全局组件引用 (将在main.py中设置)
device_manager: DeviceInstanceManager = None

def set_device_manager(manager: DeviceInstanceManager):
    """设置全局设备管理器"""
    global device_manager
    device_manager = manager

@router.post("/{device_id}/start", response_model=ControlResponse)
async def start_device(device_id: str):
    """启动指定设备"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        # 检查设备实例是否存在，不存在则创建
        instance = device_manager.get_device_instance(device_id)
        if not instance:
            # 使用默认配置创建设备实例
            from config_loader import Config
            stream_config = Config.get_stream_config()
            audio_config = Config.get_audio_config()
            
            instance = device_manager.create_device_instance(
                device_id, stream_config, audio_config
            )
            logger.info(f"为设备 {device_id} 创建了新实例")
        
        # 启动设备
        success = await device_manager.start_device(device_id)
        
        if success:
            return ControlResponse.success(f"设备 {device_id} 启动成功")
        else:
            return ControlResponse.error(f"设备 {device_id} 启动失败: {instance.last_error}")
            
    except DeviceConflictError as e:
        return ControlResponse.error(f"设备冲突: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"启动设备 {device_id} 失败: {e}")
        return ControlResponse.error(f"启动失败: {str(e)}")

@router.post("/{device_id}/stop", response_model=ControlResponse)
async def stop_device(device_id: str):
    """停止指定设备"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        success = await device_manager.stop_device(device_id)
        
        if success:
            return ControlResponse.success(f"设备 {device_id} 停止成功")
        else:
            return ControlResponse.error(f"设备 {device_id} 停止失败")
            
    except Exception as e:
        logger.error(f"停止设备 {device_id} 失败: {e}")
        return ControlResponse.error(f"停止失败: {str(e)}")

@router.get("/{device_id}/status")
async def get_device_detailed_status(device_id: str):
    """获取指定设备的详细状态"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        instance = device_manager.get_device_instance(device_id)
        
        if not instance:
            # 设备实例不存在，但设备可能存在于系统中
            available_devices = device_manager.get_available_devices()
            device_info = next((d for d in available_devices if d['id'] == device_id), None)
            
            if not device_info:
                raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
            
            return {
                "device_id": device_id,
                "device_name": device_info['name'],
                "system_index": device_info['system_index'],
                "state": "not_created",
                "instance_exists": False,
                "device_info": device_info,
                "timestamp": __import__('time').time() * 1000
            }
        
        # 获取设备实例状态
        status = instance.get_status()
        status["instance_exists"] = True
        status["timestamp"] = __import__('time').time() * 1000
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取设备状态失败 {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

@router.get("/{device_id}/stream")
async def get_device_stream(device_id: str, request: Request):
    """获取指定设备的SSE数据流"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        instance = device_manager.get_device_instance(device_id)
        
        if not instance:
            raise HTTPException(status_code=404, detail=f"设备实例不存在: {device_id}")
        
        if instance.state.value != "running":
            raise HTTPException(
                status_code=400, 
                detail=f"设备未运行，当前状态: {instance.state.value}"
            )
        
        logger.info(f"新的SSE连接到设备 {device_id}: {request.client.host}:{request.client.port}")
        
        # 获取设备专属的数据流
        return await instance.get_stream_generator(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建设备流失败 {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"创建数据流失败: {str(e)}")

@router.post("/{device_id}/config/stream", response_model=ControlResponse)
async def update_device_stream_config(device_id: str, config: StreamConfig):
    """更新指定设备的流配置"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        instance = device_manager.get_device_instance(device_id)
        
        if not instance:
            raise HTTPException(status_code=404, detail=f"设备实例不存在: {device_id}")
        
        instance.update_stream_config(config)
        
        return ControlResponse.success(
            f"设备 {device_id} 流配置更新成功，目标FPS: {config.target_fps}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新设备流配置失败 {device_id}: {e}")
        return ControlResponse.error(f"配置更新失败: {str(e)}")

@router.get("/{device_id}/config/stream", response_model=StreamConfig)
async def get_device_stream_config(device_id: str):
    """获取指定设备的流配置"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        instance = device_manager.get_device_instance(device_id)
        
        if not instance:
            raise HTTPException(status_code=404, detail=f"设备实例不存在: {device_id}")
        
        return instance.stream_config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取设备流配置失败 {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@router.post("/{device_id}/config/audio", response_model=ControlResponse)
async def update_device_audio_config(device_id: str, config: AudioConfig):
    """更新指定设备的音频配置（需要重启设备）"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        instance = device_manager.get_device_instance(device_id)
        
        if not instance:
            raise HTTPException(status_code=404, detail=f"设备实例不存在: {device_id}")
        
        instance.update_audio_config(config)
        
        restart_needed = instance.state.value == "running"
        message = f"设备 {device_id} 音频配置更新成功"
        if restart_needed:
            message += "，需要重启设备才能生效"
        
        return ControlResponse.success(message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新设备音频配置失败 {device_id}: {e}")
        return ControlResponse.error(f"配置更新失败: {str(e)}")

@router.get("/{device_id}/config/audio", response_model=AudioConfig)
async def get_device_audio_config(device_id: str):
    """获取指定设备的音频配置"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        instance = device_manager.get_device_instance(device_id)
        
        if not instance:
            raise HTTPException(status_code=404, detail=f"设备实例不存在: {device_id}")
        
        return instance.audio_config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取设备音频配置失败 {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@router.delete("/{device_id}")
async def remove_device_instance(device_id: str):
    """移除设备实例"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        success = await device_manager.remove_device_instance(device_id)
        
        return {
            "success": success,
            "message": f"设备实例 {device_id} 已移除",
            "timestamp": __import__('time').time() * 1000
        }
        
    except Exception as e:
        logger.error(f"移除设备实例失败 {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"移除失败: {str(e)}")

@router.post("/{device_id}/restart", response_model=ControlResponse)
async def restart_device(device_id: str):
    """重启指定设备"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        instance = device_manager.get_device_instance(device_id)
        
        if not instance:
            raise HTTPException(status_code=404, detail=f"设备实例不存在: {device_id}")
        
        # 停止设备
        stop_success = await device_manager.stop_device(device_id)
        if not stop_success:
            return ControlResponse.error(f"重启失败：无法停止设备 {device_id}")
        
        # 稍等片刻
        import asyncio
        await asyncio.sleep(1)
        
        # 重新启动
        start_success = await device_manager.start_device(device_id)
        if start_success:
            return ControlResponse.success(f"设备 {device_id} 重启成功")
        else:
            return ControlResponse.error(f"重启失败：无法启动设备 {device_id}: {instance.last_error}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重启设备失败 {device_id}: {e}")
        return ControlResponse.error(f"重启失败: {str(e)}")

# 批量操作API
@router.post("/batch/start")
async def start_multiple_devices(device_ids: list[str]):
    """批量启动多个设备"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    results = {}
    
    for device_id in device_ids:
        try:
            # 检查或创建设备实例
            instance = device_manager.get_device_instance(device_id)
            if not instance:
                from config_loader import Config
                stream_config = Config.get_stream_config()
                audio_config = Config.get_audio_config()
                
                instance = device_manager.create_device_instance(
                    device_id, stream_config, audio_config
                )
            
            success = await device_manager.start_device(device_id)
            results[device_id] = {
                "success": success,
                "message": "启动成功" if success else f"启动失败: {instance.last_error}"
            }
            
        except Exception as e:
            results[device_id] = {
                "success": False,
                "message": f"启动失败: {str(e)}"
            }
    
    return {
        "results": results,
        "timestamp": __import__('time').time() * 1000
    }

@router.post("/batch/stop")
async def stop_multiple_devices(device_ids: list[str]):
    """批量停止多个设备"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    results = {}
    
    for device_id in device_ids:
        try:
            success = await device_manager.stop_device(device_id)
            results[device_id] = {
                "success": success,
                "message": "停止成功" if success else "停止失败"
            }
            
        except Exception as e:
            results[device_id] = {
                "success": False,
                "message": f"停止失败: {str(e)}"
            }
    
    return {
        "results": results,
        "timestamp": __import__('time').time() * 1000
    }