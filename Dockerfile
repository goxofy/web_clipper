# 使用官方 Python 轻量级镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
# 防止 Python 生成 .pyc 文件
ENV PYTHONDONTWRITEBYTECODE=1
# 确保 Python 输出不被缓存
ENV PYTHONUNBUFFERED=1

# 更新 pip
RUN pip install --no-cache-dir --upgrade pip

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建 uploads 目录
RUN mkdir -p uploads

# 暴露端口 (默认 65331)
EXPOSE 65331

# 启动命令
CMD ["python", "main.py"]
