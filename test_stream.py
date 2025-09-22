#!/usr/bin/env python3
"""
简单的SSE流测试工具
用于验证60FPS数据流是否正常工作
"""
import time
import requests
import json
from datetime import datetime

def test_sse_stream():
    print("🎯 测试SSE流接收60FPS数据")
    print("=" * 50)
    
    url = "http://localhost:8380/api/stream"
    
    try:
        # 使用requests的流模式连接SSE
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        frame_count = 0
        start_time = time.time()
        last_frame_time = start_time
        frame_times = []
        
        print(f"已连接到 {url}")
        print("正在接收数据流...")
        print()
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                
                # 处理SSE数据行
                if line.startswith('data: '):
                    try:
                        data_json = line[6:]  # 去掉 'data: ' 前缀
                        data = json.loads(data_json)
                        
                        # 跳过连接确认和心跳消息
                        if 'type' in data:
                            if data['type'] == 'connected':
                                print(f"✅ 连接确认: {data.get('message', '')}")
                            elif data['type'] == 'heartbeat':
                                print("💓 心跳")
                            continue
                        
                        # 处理FFT数据帧
                        if 'data_compressed' in data:
                            current_time = time.time()
                            frame_count += 1
                            
                            # 计算时间间隔
                            time_since_last = current_time - last_frame_time
                            frame_times.append(time_since_last)
                            
                            # 每10帧显示一次统计
                            if frame_count % 10 == 0:
                                # 计算平均FPS
                                if len(frame_times) > 1:
                                    avg_interval = sum(frame_times[-10:]) / min(len(frame_times), 10)
                                    measured_fps = 1.0 / avg_interval if avg_interval > 0 else 0
                                else:
                                    measured_fps = 0
                                
                                elapsed = current_time - start_time
                                overall_fps = frame_count / elapsed if elapsed > 0 else 0
                                
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                backend_fps = data.get('fps', 0)
                                peak_freq = data.get('peak_frequency_hz', 0) / 1000  # Convert to kHz
                                
                                print(f"[{timestamp}] 帧#{frame_count:4d} | "
                                      f"后端FPS:{backend_fps:5.1f} | "
                                      f"测量FPS:{measured_fps:5.1f} | "
                                      f"平均FPS:{overall_fps:5.1f} | "
                                      f"峰值:{peak_freq:6.1f}kHz")
                            
                            last_frame_time = current_time
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析错误: {e}")
                    except Exception as e:
                        print(f"❌ 数据处理错误: {e}")
                        
    except requests.exceptions.RequestException as e:
        print(f"❌ 连接错误: {e}")
    except KeyboardInterrupt:
        print("\n👋 测试中断")
        
    finally:
        if frame_count > 0:
            total_time = time.time() - start_time
            avg_fps = frame_count / total_time
            print(f"\n📊 测试总结:")
            print(f"   总帧数: {frame_count}")
            print(f"   测试时长: {total_time:.1f}秒")
            print(f"   平均FPS: {avg_fps:.1f}")
        else:
            print("\n❌ 未接收到任何数据帧")

if __name__ == "__main__":
    test_sse_stream()