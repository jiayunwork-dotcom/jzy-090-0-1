FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY tests ./tests

EXPOSE 8000

# 默认启动服务；容器内执行测试：docker run --rm <image> pytest -q
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
