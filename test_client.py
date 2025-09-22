#!/usr/bin/env python3
"""
简单的测试客户端
用于验证headless超声波服务器功能
"""
import requests
import json
import time
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_URL = "http://localhost:8380"

def test_status():
    """测试状态API"""
    print("🔍 测试状态API...")
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态API正常")
            print(f"   运行状态: {'🟢' if data['is_running'] else '🔴'}")
            print(f"   当前FPS: {data['current_fps']:.1f}")
            print(f"   连接客户端: {data['connected_clients']}")
            print(f"   音频设备: {data['audio_device_name'] or '未知'}")
            return True
        else:
            print(f"❌ 状态API错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 状态API异常: {e}")
        return False

def test_start():
    """测试启动API"""
    print("\n🚀 测试启动API...")
    try:
        response = requests.post(f"{BASE_URL}/api/start", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 启动API正常: {data['message']}")
            return True
        else:
            print(f"❌ 启动API错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 启动API异常: {e}")
        return False

def test_devices():
    """测试设备API"""
    print("\n🎤 测试设备API...")
    try:
        response = requests.get(f"{BASE_URL}/api/devices", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 设备API正常")
            print(f"   可用输入设备: {len(data['devices'])}个")
            for i, device in enumerate(data['devices'][:3]):  # 只显示前3个
                print(f"   {i}: {device['name']}")
            return True
        else:
            print(f"❌ 设备API错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 设备API异常: {e}")
        return False

def test_sse_basic():
    """测试SSE基本连接"""
    print("\n📡 测试SSE连接...")
    try:
        import requests
        response = requests.get(f"{BASE_URL}/api/stream/test", 
                              stream=True, timeout=10)
        
        if response.status_code == 200:
            print("✅ SSE连接建立成功")
            
            # 读取几行数据
            lines_read = 0
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])  # 去掉'data: '前缀
                        if data.get('type') == 'test_data':
                            print(f"   📊 收到测试数据: {data['message']}")
                            lines_read += 1
                            if lines_read >= 3:  # 只读3条就退出
                                break
                    except json.JSONDecodeError:
                        pass
            
            return True
        else:
            print(f"❌ SSE连接错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ SSE连接异常: {e}")
        return False

def test_web_interface():
    """测试Web界面"""
    print("\n🌐 测试Web界面...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            if "Headless超声波可视化器" in response.text:
                print("✅ Web界面正常")
                return True
            else:
                print("⚠️ Web界面内容异常")
                return False
        else:
            print(f"❌ Web界面错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Web界面异常: {e}")
        return False

def main():
    """主测试流程"""
    print("🎵 Headless超声波服务器测试")
    print("=" * 50)
    
    # 基本功能测试
    tests = [
        ("状态API", test_status),
        ("启动API", test_start), 
        ("设备API", test_devices),
        ("Web界面", test_web_interface),
        ("SSE连接", test_sse_basic),
    ]
    
    passed = 0
    for name, test_func in tests:
        if test_func():
            passed += 1
        time.sleep(0.5)  # 小延迟
    
    print(f"\n📊 测试结果: {passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        print("🎉 所有测试通过！服务器运行正常")
        print(f"\n访问地址:")
        print(f"  Web界面: {BASE_URL}")
        print(f"  API文档: {BASE_URL}/docs")
        print(f"  SSE流: {BASE_URL}/api/stream")
    else:
        print("⚠️ 部分测试失败，请检查服务器状态")
    
    # 实时状态监控
    print(f"\n⏱️ 实时状态监控 (按Ctrl+C退出):")
    try:
        while True:
            try:
                response = requests.get(f"{BASE_URL}/api/status", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    status = "🟢 运行中" if data['is_running'] else "🔴 停止"
                    print(f"\r{status} | FPS: {data['current_fps']:5.1f} | "
                          f"客户端: {data['connected_clients']} | "
                          f"发送帧: {data['total_frames_sent']}", end="")
                else:
                    print(f"\r❌ 状态获取失败: {response.status_code}", end="")
            except:
                print(f"\r❌ 连接失败", end="")
            
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n👋 测试结束")

if __name__ == "__main__":
    main()