#!/usr/bin/env python3
"""
启动脚本
"""
import uvicorn
from config import Config

if __name__ == "__main__":
    print("🎵 启动Headless超声波可视化器...")
    print(f"服务器地址: http://{Config.HOST}:{Config.PORT}")
    print("按 Ctrl+C 停止服务")
    
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL.lower()
    )