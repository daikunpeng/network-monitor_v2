FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    iperf3 \
    iputils-ping \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制项目文件
COPY requirements.txt .
COPY app/ ./app/
COPY static/ ./static/
COPY templates/ ./templates/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python", "app/app.py"] 