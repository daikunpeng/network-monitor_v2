# Network Monitor v2

这是一个基于 Docker 的实时网络性能监控工具，用于监控和可视化两个 IP 地址之间的网络性能指标。该工具提供了直观的 Web 界面，支持实时数据可视化，适用于网络性能测试和监控场景。

## 功能特点

- 实时监控多个网络性能指标：
  - 网络延迟（Ping）
  - WiFi 信号质量（仅限 Linux 系统）
  - 网络吞吐量
  - 丢包率统计
- 基于 Web 的实时可视化界面
- 数据实时更新和滚动显示
- 完整的 Docker 封装，便于部署
- 响应式设计，支持各种设备访问

## 技术栈

### 后端
- Python 3.9+
- Flask (Web 框架)
- Flask-SocketIO (WebSocket 支持)
- iperf3 (带宽测试)
- eventlet (异步支持)
- psutil (系统和性能信息)
- ping3 (网络延迟测试)

### 前端
- HTML5
- CSS3 (Bootstrap 5)
- JavaScript
- Chart.js (图表可视化)
- Socket.IO (实时数据传输)

## 安装说明

### 前置条件

- Docker
- Docker Compose (可选)

### 安装步骤

1. 克隆仓库：
```bash
git clone <repository-url>
cd network-monitor_v2
```

2. 构建 Docker 镜像：
```bash
docker build -t network-monitor .
```

3. 运行容器：
```bash
docker run -p 8080:8080 netwok-monitor_v2
```

注意：使用 `--network host` 选项是为了让容器能够访问主机的网络接口，这对于网络监控是必要的。

## 使用方法
0. 确保目标IP的终端已开启 iperf3 服务
```bash
iperf3 -s
```

1. 启动容器后，打开浏览器访问：
```
http://localhost:8080
```

1. 在界面上输入要监控的目标 IP 地址

2. 点击"开始监控"按钮开始实时监控

3. 监控界面将显示以下四个实时更新的图表：
   - 网络延迟图表
   - WiFi 信号质量图表
   - 网络吞吐量图表
   - 丢包率统计图表

4. 需要停止监控时，点击"停止监控"按钮

## 注意事项

1. WiFi 信号质量监控功能仅在 Linux 系统上有效
2. 某些网络监控功能可能需要 root 权限
3. 为了获得最佳性能监控效果，建议在本地网络环境中使用
4. 数据更新频率为每秒一次，可以根据需要在代码中调整

## 项目结构

```
network-monitor_v2/
├── app/
│   └── app.py
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   └── index.html
├── Dockerfile
├── requirements.txt
└── README.md
```

## 贡献指南

欢迎提��� Issue 和 Pull Request 来帮助改进这个项目。

## 许可证

MIT License 