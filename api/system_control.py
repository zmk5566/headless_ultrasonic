#!/usr/bin/env python3
"""
系统级控制API端点
提供多设备管理、系统状态和全局操作
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging

from models import ControlResponse
from core import DeviceInstanceManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/system", tags=["system-control"])

# 全局组件引用
device_manager: DeviceInstanceManager = None

def set_device_manager(manager: DeviceInstanceManager):
    """设置全局设备管理器"""
    global device_manager
    device_manager = manager

@router.get("/status")
async def get_system_status():
    """获取系统整体状态"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        # 获取设备管理器统计
        manager_stats = device_manager.get_manager_stats()
        
        # 获取可用设备列表
        available_devices = device_manager.get_available_devices()
        
        # 获取所有设备实例状态
        device_instances = {}
        for device_id, instance in device_manager.get_all_device_instances().items():
            device_instances[device_id] = {
                "state": instance.state.value,
                "device_name": instance.device_name,
                "last_error": instance.last_error,
                "stats": instance.stats
            }
        
        return {
            "manager_stats": manager_stats,
            "available_devices": available_devices,
            "device_instances": device_instances,
            "timestamp": __import__('time').time() * 1000
        }
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")

@router.get("/devices")
async def list_all_devices():
    """列出所有设备（增强版，包含实例状态）"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        devices = device_manager.get_available_devices()
        
        # 为每个设备添加详细的实例信息
        for device in devices:
            device_id = device['id']
            instance = device_manager.get_device_instance(device_id)
            
            if instance:
                device['instance_info'] = {
                    "exists": True,
                    "state": instance.state.value,
                    "last_error": instance.last_error,
                    "stats": instance.stats
                }
            else:
                device['instance_info'] = {
                    "exists": False,
                    "state": "not_created",
                    "last_error": None,
                    "stats": None
                }
        
        return {
            "devices": devices,
            "total_devices": len(devices),
            "device_mapping_stats": device_manager.device_id_manager.get_mapping_stats(),
            "timestamp": __import__('time').time() * 1000
        }
        
    except Exception as e:
        logger.error(f"列出设备失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出设备失败: {str(e)}")

@router.post("/devices/refresh")
async def refresh_device_list():
    """刷新设备列表（重新扫描系统设备）"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        # 获取最新的设备列表，这会触发设备映射的清理和更新
        devices = device_manager.get_available_devices()
        
        return {
            "message": "设备列表已刷新",
            "devices_count": len(devices),
            "devices": devices,
            "timestamp": __import__('time').time() * 1000
        }
        
    except Exception as e:
        logger.error(f"刷新设备列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"刷新失败: {str(e)}")

@router.post("/cleanup")
async def cleanup_system():
    """系统清理（清理错误设备、无效映射等）"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        # 清理错误设备
        await device_manager.cleanup_error_devices()
        
        # 清理设备映射
        import sounddevice as sd
        devices = sd.query_devices()
        device_manager.device_id_manager.cleanup_missing_devices(devices)
        
        return {
            "message": "系统清理完成",
            "timestamp": __import__('time').time() * 1000
        }
        
    except Exception as e:
        logger.error(f"系统清理失败: {e}")
        raise HTTPException(status_code=500, detail=f"系统清理失败: {str(e)}")

@router.post("/stop-all")
async def stop_all_devices():
    """停止所有运行中的设备"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        await device_manager.stop_all_devices()
        
        return {
            "message": "所有设备已停止",
            "timestamp": __import__('time').time() * 1000
        }
        
    except Exception as e:
        logger.error(f"停止所有设备失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止失败: {str(e)}")

@router.get("/health")
async def system_health_check():
    """系统健康检查"""
    if not device_manager:
        return {
            "status": "unhealthy",
            "reason": "设备管理器未初始化",
            "timestamp": __import__('time').time() * 1000
        }
    
    try:
        manager_stats = device_manager.get_manager_stats()
        
        # 健康检查逻辑
        is_healthy = True
        issues = []
        
        # 检查错误设备数量
        if manager_stats["error_instances"] > manager_stats["total_instances"] * 0.5:
            is_healthy = False
            issues.append("错误设备数量过多")
        
        # 检查资源监控状态
        if not manager_stats["resource_monitor_active"]:
            issues.append("资源监控未激活")
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "issues": issues,
            "manager_stats": manager_stats,
            "timestamp": __import__('time').time() * 1000
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "reason": str(e),
            "timestamp": __import__('time').time() * 1000
        }

@router.get("/performance")
async def get_system_performance():
    """获取系统性能统计"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    try:
        import psutil
        import sys
        
        # 系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # 进程资源使用情况
        process = psutil.Process()
        process_memory = process.memory_info()
        process_cpu = process.cpu_percent()
        
        # 设备统计
        manager_stats = device_manager.get_manager_stats()
        
        # 计算总处理帧数和发送帧数
        total_frames_processed = 0
        total_frames_sent = 0
        
        for instance in device_manager.get_all_device_instances().values():
            total_frames_processed += instance.stats.get("frames_processed", 0)
            total_frames_sent += instance.stats.get("frames_sent", 0)
        
        return {
            "system_resources": {
                "cpu_percent": cpu_percent,
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_percent": memory.percent
            },
            "process_resources": {
                "memory_mb": round(process_memory.rss / (1024**2), 2),
                "cpu_percent": process_cpu,
                "python_version": sys.version,
                "thread_count": process.num_threads()
            },
            "device_performance": {
                "total_devices": manager_stats["total_instances"],
                "running_devices": manager_stats["running_instances"],
                "total_frames_processed": total_frames_processed,
                "total_frames_sent": total_frames_sent
            },
            "timestamp": __import__('time').time() * 1000
        }
        
    except ImportError:
        # psutil 未安装时的降级响应
        manager_stats = device_manager.get_manager_stats()
        
        return {
            "message": "完整性能监控需要安装psutil",
            "basic_stats": manager_stats,
            "timestamp": __import__('time').time() * 1000
        }
    except Exception as e:
        logger.error(f"获取性能统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {str(e)}")

@router.get("/config/limits")
async def get_system_limits():
    """获取系统限制配置"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    return {
        "max_concurrent_devices": device_manager.max_concurrent_devices,
        "current_device_count": len(device_manager.device_instances),
        "running_device_count": len([
            d for d in device_manager.device_instances.values() 
            if d.state.value == "running"
        ]),
        "timestamp": __import__('time').time() * 1000
    }

@router.post("/config/limits")
async def update_system_limits(max_concurrent_devices: int):
    """更新系统限制配置"""
    if not device_manager:
        raise HTTPException(status_code=503, detail="设备管理器未初始化")
    
    if max_concurrent_devices < 1 or max_concurrent_devices > 16:
        raise HTTPException(
            status_code=400, 
            detail="最大并发设备数必须在1-16之间"
        )
    
    device_manager.max_concurrent_devices = max_concurrent_devices
    
    return {
        "message": f"系统限制已更新，最大并发设备数: {max_concurrent_devices}",
        "max_concurrent_devices": max_concurrent_devices,
        "timestamp": __import__('time').time() * 1000
    }