from flask import Flask, render_template, request
from flask_socketio import SocketIO
import iperf3
import time
import threading
from ping3 import ping
import psutil
import json
import os
import subprocess
import platform
from dotenv import load_dotenv

load_dotenv()

# 修改模板路径
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)
           
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')  # 使用线程模式

# 全局变量
target_ip = None
iperf3_server = None
monitoring_active = False
monitor_thread = None
last_bytes_sent = 0
last_bytes_recv = 0
last_time = None

def ping_host(host):
    """使用系统ping命令"""
    try:
        # 在Docker容器中使用Linux的ping命令
        cmd = ['ping', '-c', '1', host]
            
        print(f"Executing ping command: {' '.join(cmd)}")  # 调试信息
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        print(f"Ping output: {result.stdout}")  # 调试信息
        
        if result.returncode == 0:
            # 从输出中提取时间
            for line in result.stdout.split('\n'):
                if 'time=' in line:
                    time_str = line.split('time=')[1].split()[0]
                    # 移除ms单位
                    time_str = time_str.replace('ms', '').strip()
                    return float(time_str)
        return None
    except Exception as e:
        print(f"Ping error: {e}")
        return None

def run_iperf3_test(target_ip):
    """运行iperf3测试获取吞吐量"""
    try:
        client = iperf3.Client()
        client.duration = 1  # 测试时长1秒
        client.server_hostname = target_ip
        client.port = 5201  # iperf3默认端口
        client.protocol = 'tcp'
        
        print(f"Starting iperf3 test to {target_ip}")  # 调试信息
        result = client.run()
        
        if result.error:
            print(f"Iperf3 error: {result.error}")  # 调试信息
            return 0
            
        # 转换为MB/s (result.sent_bytes是以字节为单位的)
        throughput = result.sent_bytes / (1024 * 1024)  # MB/s
        print(f"Iperf3 throughput: {throughput} MB/s")  # 调试信息
        return throughput
        
    except Exception as e:
        print(f"Error running iperf3 test: {e}")  # 调试信息
        return 0

def get_network_stats():
    """获取网络统计信息"""
    if not target_ip:
        print("No target IP set")  # 调试信息
        return None
    
    try:
        current_time = time.time()
        
        # 使用系统ping命令
        delay = ping_host(target_ip)
        print(f"Ping result for {target_ip}: {delay}ms")  # 调试信息
        
        # 获取WiFi信号质量（仅在Linux系统上有效，且不在容器中）
        wifi_quality = None
        if not os.path.exists('/proc/net/wireless'):
            print("WiFi quality monitoring not available in this environment")  # 调试信息
        else:
            try:
                with open('/proc/net/wireless') as f:
                    for line in f:
                        if 'wlan0' in line:
                            wifi_quality = float(line.split()[2].replace('.', ''))
            except Exception as e:
                print(f"Error getting WiFi quality: {e}")  # 调试信息
        
        # 使用iperf3获取吞吐量
        throughput = run_iperf3_test(target_ip)
        
        # 获取网络接口统计（用于丢包率计算）
        net_stats = psutil.net_io_counters()
        
        stats = {
            'timestamp': current_time,
            'delay': delay if delay is not None else 0,
            'wifi_quality': wifi_quality if wifi_quality is not None else 0,
            'throughput': throughput,
            'packets_sent': net_stats.packets_sent,
            'packets_recv': net_stats.packets_recv,
            'errin': net_stats.errin,
            'errout': net_stats.errout,
            'dropin': net_stats.dropin,
            'dropout': net_stats.dropout
        }
        print(f"Network stats: {json.dumps(stats, indent=2)}")  # 调试信息
        return stats
    except Exception as e:
        print(f"Error getting network stats: {e}")
        return None

def monitor_network():
    """网络监控主循环"""
    global monitoring_active
    print(f"Starting monitoring for IP: {target_ip}")  # 调试信息
    try:
        while monitoring_active:
            print(f"Monitoring loop iteration for IP: {target_ip}")  # 调试信息
            stats = get_network_stats()
            if stats:
                print("Emitting network stats via socketio")  # 调试信息
                try:
                    socketio.emit('network_stats', stats, namespace='/')
                    print("Successfully emitted stats")  # 调试信息
                except Exception as e:
                    print(f"Error emitting stats: {e}")  # 调试信息
            time.sleep(1)
    except Exception as e:
        print(f"Error in monitoring thread: {e}")  # 调试信息
    finally:
        print("Monitoring stopped")  # 调试信息
        monitoring_active = False

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_monitoring')
def handle_start_monitoring(data):
    """开始监控"""
    global target_ip, monitoring_active, monitor_thread
    target_ip = data.get('target_ip')
    print(f"Received start_monitoring request for IP: {target_ip}")  # 调试信息
    
    if monitor_thread and monitor_thread.is_alive():
        print("Previous monitoring thread is still running")  # 调试信息
        return
        
    if not monitoring_active and target_ip:
        try:
            monitoring_active = True
            monitor_thread = threading.Thread(target=monitor_network)
            monitor_thread.daemon = True  # 设置为守护线程
            monitor_thread.start()
            print(f"Monitoring thread started with ID: {monitor_thread.ident}")  # 调试信息
        except Exception as e:
            print(f"Error starting monitoring thread: {e}")  # 调试信息
            monitoring_active = False

@socketio.on('stop_monitoring')
def handle_stop_monitoring():
    """停止监控"""
    global monitoring_active, monitor_thread
    print("Received stop_monitoring request")  # 调试信息
    monitoring_active = False
    if monitor_thread:
        print(f"Waiting for monitoring thread {monitor_thread.ident} to stop")  # 调试信息

@socketio.on('connect')
def handle_connect():
    print("Client connected")  # 调试信息
    print(f"Socket ID: {request.sid}")  # 调试信息

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")  # 调试信息

if __name__ == '__main__':
    print(f"Template directory: {template_dir}")
    print(f"Static directory: {static_dir}")
    print("Starting Flask-SocketIO server...")  # 调试信息
    socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True) 