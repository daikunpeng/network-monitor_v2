from flask import Flask, render_template
from flask_socketio import SocketIO
import iperf3
import time
import threading
from ping3 import ping
import psutil
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
socketio = SocketIO(app)

# 全局变量
target_ip = None
iperf3_server = None
monitoring_active = False

def get_network_stats():
    """获取网络统计信息"""
    if not target_ip:
        return None
    
    try:
        # 测试延迟
        delay = ping(target_ip, unit='ms')
        
        # 获取WiFi信号质量（仅在Linux系统上有效）
        wifi_quality = None
        try:
            with open('/proc/net/wireless') as f:
                for line in f:
                    if 'wlan0' in line:
                        wifi_quality = float(line.split()[2].replace('.', ''))
        except:
            pass
        
        # 获取网络接口统计
        net_stats = psutil.net_io_counters()
        
        return {
            'timestamp': time.time(),
            'delay': delay,
            'wifi_quality': wifi_quality,
            'bytes_sent': net_stats.bytes_sent,
            'bytes_recv': net_stats.bytes_recv,
            'packets_sent': net_stats.packets_sent,
            'packets_recv': net_stats.packets_recv,
            'errin': net_stats.errin,
            'errout': net_stats.errout,
            'dropin': net_stats.dropin,
            'dropout': net_stats.dropout
        }
    except Exception as e:
        print(f"Error getting network stats: {e}")
        return None

def monitor_network():
    """网络监控主循环"""
    global monitoring_active
    while monitoring_active:
        stats = get_network_stats()
        if stats:
            socketio.emit('network_stats', stats)
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_monitoring')
def handle_start_monitoring(data):
    """开始监控"""
    global target_ip, monitoring_active
    target_ip = data.get('target_ip')
    if not monitoring_active and target_ip:
        monitoring_active = True
        threading.Thread(target=monitor_network).start()

@socketio.on('stop_monitoring')
def handle_stop_monitoring():
    """停止监控"""
    global monitoring_active
    monitoring_active = False

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True) 