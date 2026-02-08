# Hugging Face Spaces Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口（Hugging Face Spaces 使用 7860）
EXPOSE 7860

# 启动命令
CMD ["uvicorn", "api_service.main:app", "--host", "0.0.0.0", "--port", "7860"]
