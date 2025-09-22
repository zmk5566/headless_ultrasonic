#!/usr/bin/env python3
"""
检测帧唯一性的测试工具
分析是否存在重复或过于相似的帧数据
"""
import time
import requests
import json
import base64
import gzip
import numpy as np
from datetime import datetime
from collections import deque

def decompress_fft_data(compressed_data):
    """解压缩FFT数据"""
    try:
        binary_string = base64.b64decode(compressed_data)
        decompressed = gzip.decompress(binary_string)
        return np.frombuffer(decompressed, dtype=np.float32)
    except Exception as e:
        print(f"❌ 解压缩失败: {e}")
        return None

def calculate_frame_similarity(data1, data2):
    """计算两帧数据的相似度(0-1, 1表示完全相同)"""
    if data1 is None or data2 is None or len(data1) != len(data2):
        return 0.0
    
    # 计算相关系数
    correlation = np.corrcoef(data1, data2)[0, 1]
    if np.isnan(correlation):
        return 0.0
    
    # 计算均方根误差的归一化版本
    mse = np.mean((data1 - data2) ** 2)
    max_possible_mse = np.mean(data1 ** 2) + np.mean(data2 ** 2)
    if max_possible_mse == 0:
        return 1.0
    
    normalized_mse = mse / max_possible_mse
    mse_similarity = 1.0 - min(normalized_mse, 1.0)
    
    # 综合相关系数和MSE
    return (abs(correlation) + mse_similarity) / 2.0

def test_frame_uniqueness():
    print("🔍 测试帧数据唯一性和变化程度")
    print("=" * 60)
    
    url = "http://localhost:8380/api/stream"
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        frame_count = 0
        start_time = time.time()
        
        # 保存最近的几帧数据用于比较
        recent_frames = deque(maxlen=5)
        duplicate_count = 0
        high_similarity_count = 0
        
        # 统计信息
        similarities = []
        peak_frequencies = []
        magnitude_ranges = []
        
        print("正在分析帧数据...")
        print("格式: [时间] 帧号 | 相似度 | 峰值频率 | 幅度范围 | 状态")
        print("-" * 80)
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                
                if line.startswith('data: '):
                    try:
                        data_json = line[6:]
                        data = json.loads(data_json)
                        
                        # 跳过非FFT数据
                        if 'type' in data or 'data_compressed' not in data:
                            continue
                        
                        # 解压缩FFT数据
                        fft_data = decompress_fft_data(data['data_compressed'])
                        if fft_data is None:
                            continue
                        
                        frame_count += 1
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        
                        # 计算当前帧的统计信息
                        peak_freq = data.get('peak_frequency_hz', 0) / 1000  # kHz
                        magnitude_min = np.min(fft_data)
                        magnitude_max = np.max(fft_data)
                        magnitude_range = magnitude_max - magnitude_min
                        
                        peak_frequencies.append(peak_freq)
                        magnitude_ranges.append(magnitude_range)
                        
                        # 与最近的帧比较相似度
                        status = "新帧"
                        max_similarity = 0.0
                        
                        if recent_frames:
                            similarities_with_recent = []
                            for prev_data, prev_info in recent_frames:
                                similarity = calculate_frame_similarity(fft_data, prev_data)
                                similarities_with_recent.append(similarity)
                            
                            max_similarity = max(similarities_with_recent)
                            similarities.append(max_similarity)
                            
                            if max_similarity > 0.99:
                                duplicate_count += 1
                                status = "🔴 重复帧"
                            elif max_similarity > 0.95:
                                high_similarity_count += 1
                                status = "🟡 高相似"
                            elif max_similarity > 0.8:
                                status = "🟢 正常变化"
                            else:
                                status = "🔵 大幅变化"
                        
                        # 保存当前帧
                        recent_frames.append((fft_data, {
                            'peak_freq': peak_freq,
                            'magnitude_range': magnitude_range,
                            'timestamp': time.time()
                        }))
                        
                        # 每10帧显示一次详细信息
                        if frame_count % 10 == 0:
                            print(f"[{timestamp}] #{frame_count:3d} | "
                                  f"相似度:{max_similarity:.3f} | "
                                  f"峰值:{peak_freq:6.1f}kHz | "
                                  f"范围:{magnitude_range:6.1f}dB | "
                                  f"{status}")
                        
                        # 当达到一定帧数时显示统计报告
                        if frame_count == 100:
                            print("\n" + "="*60)
                            print("📊 100帧统计报告:")
                            if similarities:
                                avg_similarity = np.mean(similarities)
                                print(f"   平均相似度: {avg_similarity:.3f}")
                                print(f"   重复帧数: {duplicate_count} ({duplicate_count/frame_count*100:.1f}%)")
                                print(f"   高相似帧数: {high_similarity_count} ({high_similarity_count/frame_count*100:.1f}%)")
                            
                            if peak_frequencies:
                                freq_std = np.std(peak_frequencies)
                                print(f"   峰值频率标准差: {freq_std:.2f} kHz")
                            
                            if magnitude_ranges:
                                range_std = np.std(magnitude_ranges)
                                print(f"   幅度范围标准差: {range_std:.2f} dB")
                            
                            print("="*60)
                            print("继续监控...")
                        
                        # 限制测试时间
                        if time.time() - start_time > 15:  # 15秒后停止
                            break
                            
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"❌ 处理错误: {e}")
                        continue
                        
    except requests.exceptions.RequestException as e:
        print(f"❌ 连接错误: {e}")
    except KeyboardInterrupt:
        print("\n👋 测试中断")
        
    finally:
        if frame_count > 0:
            print(f"\n📋 最终统计:")
            print(f"   总帧数: {frame_count}")
            print(f"   重复帧: {duplicate_count} ({duplicate_count/frame_count*100:.1f}%)")
            print(f"   高相似帧: {high_similarity_count} ({high_similarity_count/frame_count*100:.1f}%)")
            
            if similarities:
                print(f"   平均帧间相似度: {np.mean(similarities):.3f}")
                print(f"   相似度标准差: {np.std(similarities):.3f}")
            
            if len(peak_frequencies) > 1:
                print(f"   峰值频率变化: {np.std(peak_frequencies):.2f} kHz")
            
            if len(magnitude_ranges) > 1:
                print(f"   幅度范围变化: {np.std(magnitude_ranges):.2f} dB")
                
            # 判断问题所在
            if duplicate_count / frame_count > 0.3:
                print("\n⚠️  检测到大量重复帧！这可能是导致视觉不流畅的原因。")
            elif np.mean(similarities) > 0.9:
                print("\n⚠️  帧间相似度过高！可能缺乏足够的数据变化。")
            elif np.std(peak_frequencies) < 0.1:
                print("\n⚠️  音频信号变化很小！可能环境过于安静。")
            else:
                print("\n✅ 帧数据看起来正常，问题可能在其他地方。")

if __name__ == "__main__":
    test_frame_uniqueness()