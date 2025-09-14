#!/usr/bin/env python3
"""
SSE数据流传输模块
负责管理客户端连接和数据广播
"""
import asyncio
import json
import time
import logging
from typing import Set, Optional, Dict, Any
from collections import deque
from fastapi import Request
from fastapi.responses import StreamingResponse
from models import FFTFrame, StreamConfig

logger = logging.getLogger(__name__)

class DataStreamer:
    """SSE数据流管理器"""
    
    def __init__(self, stream_config: StreamConfig):
        self.config = stream_config
        self.clients: Set[str] = set()  # 客户端ID集合
        self.client_queues: Dict[str, asyncio.Queue] = {}  # 每个客户端的数据队列
        self.is_streaming = False
        self.sequence_id = 0
        
        # 统计信息
        self.total_frames_sent = 0
        self.total_bytes_sent = 0
        self.start_time = time.time()
        self.fps_history = deque(maxlen=60)  # 记录最近60帧的时间
        
        # 自适应控制
        self.current_fps = stream_config.target_fps
        self.last_frame_time = 0
        
        logger.info(f"数据流管理器初始化完成, 目标FPS: {stream_config.target_fps}")
    
    def add_client(self, client_id: str) -> asyncio.Queue:
        """添加客户端"""
        if client_id not in self.clients:
            self.clients.add(client_id)
            self.client_queues[client_id] = asyncio.Queue(maxsize=120)  # 支持60FPS*2秒缓冲，防止帧丢失
            logger.info(f"客户端连接: {client_id} (总数: {len(self.clients)})")
        return self.client_queues[client_id]
    
    def remove_client(self, client_id: str):
        """移除客户端"""
        if client_id in self.clients:
            self.clients.remove(client_id)
            if client_id in self.client_queues:
                del self.client_queues[client_id]
            logger.info(f"客户端断开: {client_id} (总数: {len(self.clients)})")
    
    def get_client_count(self) -> int:
        """获取连接的客户端数量"""
        return len(self.clients)
    
    async def broadcast_frame(self, fft_frame: FFTFrame, frame_time: float = None):
        """广播FFT帧到所有客户端"""
        if not self.clients:
            return
        
        # 更新序列号
        self.sequence_id += 1
        fft_frame.sequence_id = self.sequence_id
        
        # 使用传入的时间戳或当前时间
        current_time = frame_time if frame_time else time.time()
        self.fps_history.append(current_time)
        if len(self.fps_history) > 1:
            time_span = self.fps_history[-1] - self.fps_history[0]
            self.current_fps = (len(self.fps_history) - 1) / time_span if time_span > 0 else 0
            fft_frame.fps = self.current_fps
        
        # 准备SSE数据
        sse_data = self._prepare_sse_data(fft_frame)
        
        # 广播到所有客户端
        disconnected_clients = []
        for client_id, queue in self.client_queues.items():
            try:
                # 非阻塞放入队列
                queue.put_nowait(sse_data)
            except asyncio.QueueFull:
                logger.warning(f"客户端 {client_id} 队列已满，丢弃帧")
            except Exception as e:
                logger.error(f"广播到客户端 {client_id} 失败: {e}")
                disconnected_clients.append(client_id)
        
        # 清理断开的客户端
        for client_id in disconnected_clients:
            self.remove_client(client_id)
        
        # 更新统计
        self.total_frames_sent += 1
        self.total_bytes_sent += len(sse_data.encode('utf-8'))
        self.last_frame_time = current_time
    
    def _prepare_sse_data(self, fft_frame: FFTFrame) -> str:
        """准备SSE数据格式"""
        # 转为JSON
        frame_json = fft_frame.json()
        
        # SSE格式
        return f"data: {frame_json}\n\n"
    
    async def create_client_stream(self, request: Request):
        """为客户端创建SSE流"""
        client_id = f"{request.client.host}:{request.client.port}_{time.time()}"
        client_queue = self.add_client(client_id)
        
        async def stream_generator():
            try:
                # 发送连接确认
                yield "data: " + json.dumps({
                    "type": "connected",
                    "client_id": client_id,
                    "timestamp": time.time() * 1000,
                    "message": "连接成功"
                }) + "\n\n"
                
                # 持续发送数据
                while True:
                    try:
                        # 等待数据，超时检查连接状态
                        data = await asyncio.wait_for(client_queue.get(), timeout=30.0)
                        yield data
                        
                        # 检查客户端是否断开
                        if await request.is_disconnected():
                            break
                            
                    except asyncio.TimeoutError:
                        # 发送心跳
                        heartbeat = "data: " + json.dumps({
                            "type": "heartbeat",
                            "timestamp": time.time() * 1000
                        }) + "\n\n"
                        yield heartbeat
                        
                    except Exception as e:
                        logger.error(f"客户端 {client_id} 流错误: {e}")
                        break
                        
            except Exception as e:
                logger.error(f"客户端 {client_id} 连接错误: {e}")
            finally:
                self.remove_client(client_id)
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    
    def should_send_frame(self, current_time: float) -> bool:
        """根据目标FPS判断是否应该发送帧"""
        if self.last_frame_time == 0:
            return True
            
        time_since_last = current_time - self.last_frame_time
        min_interval = 1.0 / self.config.target_fps
        
        return time_since_last >= min_interval
    
    def update_config(self, new_config: StreamConfig):
        """更新流配置"""
        old_fps = self.config.target_fps
        self.config = new_config
        
        if old_fps != new_config.target_fps:
            logger.info(f"目标FPS更新: {old_fps} -> {new_config.target_fps}")
    
    def get_stats(self) -> dict:
        """获取流统计信息"""
        uptime = time.time() - self.start_time
        avg_fps = self.total_frames_sent / uptime if uptime > 0 else 0
        
        return {
            "is_streaming": self.is_streaming,
            "connected_clients": len(self.clients),
            "total_frames_sent": self.total_frames_sent,
            "total_bytes_sent": self.total_bytes_sent,
            "uptime_seconds": uptime,
            "current_fps": self.current_fps,
            "average_fps": avg_fps,
            "target_fps": self.config.target_fps,
            "last_sequence_id": self.sequence_id
        }