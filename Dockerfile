FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 确保配置文件存在
RUN if [ ! -f config.py ]; then cp config.example.py config.py; fi

CMD ["python", "main.py"] 