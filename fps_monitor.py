#!/usr/bin/env python3
"""
实时FPS监控工具
"""
import requests
import time
import json
from datetime import datetime

def monitor_fps():
    base_url = "http://localhost:8380"
    
    print("🎯 开始监控实时FPS性能")
    print("=" * 50)
    
    last_frames = 0
    last_time = time.time()
    
    try:
        while True:
            try:
                # 获取详细统计
                response = requests.get(f"{base_url}/api/stats/detailed", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    
                    current_time = time.time()
                    current_frames = data["stream"].get("total_frames_sent", 0)
                    
                    # 计算实际FPS
                    time_diff = current_time - last_time
                    frame_diff = current_frames - last_frames
                    actual_fps = frame_diff / time_diff if time_diff > 0 else 0
                    
                    # 显示信息
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    target_fps = data["config"]["stream"]["target_fps"]
                    reported_fps = data["stream"].get("current_fps", 0)
                    connected = data["stream"].get("connected_clients", 0)
                    
                    print(f"[{timestamp}] 目标:{target_fps:2d}FPS | 报告:{reported_fps:5.1f}FPS | 实际:{actual_fps:5.1f}FPS | 客户端:{connected} | 总帧:{current_frames}")
                    
                    if connected == 0:
                        print("         ⚠️  无活跃客户端连接")
                    elif abs(actual_fps - target_fps) > 5:
                        print(f"         🚨 FPS差异较大: 实际{actual_fps:.1f} vs 目标{target_fps}")
                    
                    last_frames = current_frames
                    last_time = current_time
                    
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ API错误: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 连接失败: {e}")
            
            time.sleep(1)  # 每秒监控一次
            
    except KeyboardInterrupt:
        print("\n👋 监控结束")

if __name__ == "__main__":
    monitor_fps()