const socket = io();
const maxDataPoints = 50;

// 初始化图表
const charts = {
    latency: createChart('latencyChart', '网络延迟 (ms)'),
    wifi: createChart('wifiChart', 'WiFi信号质量 (%)'),
    throughput: createChart('throughputChart', '吞吐量 (MB/s)'),
    packetLoss: createChart('packetLossChart', '丢包率 (%)')
};

function createChart(canvasId, label) {
    return new Chart(document.getElementById(canvasId), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: label,
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 更新图表数据
function updateChart(chart, value, timestamp) {
    const data = chart.data.datasets[0].data;
    const labels = chart.data.labels;
    
    data.push(value);
    labels.push(new Date(timestamp * 1000).toLocaleTimeString());
    
    if (data.length > maxDataPoints) {
        data.shift();
        labels.shift();
    }
    
    chart.update();
}

// 计算丢包率
function calculatePacketLoss(stats) {
    const total = stats.packets_sent + stats.packets_recv;
    const lost = stats.dropin + stats.dropout;
    return total > 0 ? (lost / total) * 100 : 0;
}

// 计算吞吐量
function calculateThroughput(stats) {
    return (stats.bytes_recv + stats.bytes_sent) / (1024 * 1024); // Convert to MB
}

// Socket.io事件处理
socket.on('network_stats', (stats) => {
    updateChart(charts.latency, stats.delay, stats.timestamp);
    updateChart(charts.wifi, stats.wifi_quality, stats.timestamp);
    updateChart(charts.throughput, calculateThroughput(stats), stats.timestamp);
    updateChart(charts.packetLoss, calculatePacketLoss(stats), stats.timestamp);
});

// UI事件处理
document.getElementById('start-btn').addEventListener('click', () => {
    const targetIp = document.getElementById('target-ip').value;
    if (targetIp) {
        socket.emit('start_monitoring', { target_ip: targetIp });
        document.getElementById('start-btn').disabled = true;
        document.getElementById('stop-btn').disabled = false;
        document.getElementById('target-ip').disabled = true;
    }
});

document.getElementById('stop-btn').addEventListener('click', () => {
    socket.emit('stop_monitoring');
    document.getElementById('start-btn').disabled = false;
    document.getElementById('stop-btn').disabled = true;
    document.getElementById('target-ip').disabled = false;
}); 