# 多阶段构建 - 后端
FROM python:3.11-slim as backend-builder

WORKDIR /app

# 使用阿里云 pip 镜像，失败时回退到官方 PyPI
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    || pip install --no-cache-dir -i https://pypi.org/simple -r requirements.txt

# 复制源码
COPY . .

# 运行镜像
FROM python:3.11-slim

WORKDIR /app

# 使用阿里云 pip 镜像
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin
COPY . .

# 创建日志目录
RUN mkdir -p logs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
