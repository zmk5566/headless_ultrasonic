#!/usr/bin/env python3
"""
SSE流传输API端点
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["stream"])

# 全局数据流管理器引用 (将在main.py中设置)
data_streamer = None

def set_data_streamer(streamer):
    """设置全局数据流管理器"""
    global data_streamer
    data_streamer = streamer

@router.get("/stream")
async def stream_fft_data(request: Request):
    """SSE FFT数据流端点
    
    这个端点提供Server-Sent Events流，实时推送FFT数据
    
    返回格式:
    ```
    data: {"timestamp": 1699123456789, "sequence_id": 123, "fft_data": "...", ...}
    
    ```
    
    前端连接示例:
    ```javascript
    const eventSource = new EventSource('/api/stream');
    eventSource.onmessage = function(event) {
        const fftFrame = JSON.parse(event.data);
        console.log('收到FFT数据:', fftFrame);
    };
    ```
    """
    if not data_streamer:
        raise HTTPException(status_code=503, detail="数据流服务未启动")
    
    logger.info(f"新的SSE连接: {request.client.host}:{request.client.port}")
    
    try:
        return await data_streamer.create_client_stream(request)
    except Exception as e:
        logger.error(f"创建SSE流失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建数据流失败: {str(e)}")

@router.get("/stream/stats")
async def get_stream_stats():
    """获取流传输统计信息"""
    if not data_streamer:
        raise HTTPException(status_code=503, detail="数据流服务未启动")
    
    return data_streamer.get_stats()

@router.get("/stream/test")
async def test_sse(request: Request):
    """测试SSE连接端点
    
    用于测试SSE连接是否正常工作，每秒发送一个时间戳
    """
    import asyncio
    import json
    import time
    
    async def test_generator():
        counter = 0
        try:
            # 发送连接确认
            yield "data: " + json.dumps({
                "type": "test_start",
                "message": "SSE测试开始",
                "timestamp": time.time() * 1000
            }) + "\n\n"
            
            # 每秒发送测试数据
            while counter < 60:  # 测试1分钟
                if await request.is_disconnected():
                    break
                    
                test_data = {
                    "type": "test_data",
                    "counter": counter,
                    "timestamp": time.time() * 1000,
                    "message": f"测试消息 #{counter}"
                }
                
                yield f"data: {json.dumps(test_data)}\n\n"
                
                counter += 1
                await asyncio.sleep(1.0)
                
        except Exception as e:
            error_data = {
                "type": "test_error", 
                "error": str(e),
                "timestamp": time.time() * 1000
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        test_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )