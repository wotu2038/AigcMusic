# Django全栈应用Dockerfile
# 支持Web、Admin和API

FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY backend/requirements*.txt ./

# 创建虚拟环境并安装Python依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 生产阶段
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 创建非root用户
RUN useradd -m -u 1000 django && \
    chown -R django:django /app

# 复制项目文件
COPY --chown=django:django backend/ /app/

# 创建必要的目录
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R django:django /app/staticfiles /app/media

# 切换到非root用户
USER django

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# 默认启动命令（开发环境使用runserver，生产环境使用gunicorn）
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

