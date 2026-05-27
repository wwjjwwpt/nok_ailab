#!/usr/bin/env python3
"""
CentOS 7 部署脚本 - 先安装 Docker
"""
import paramiko
import os
import io
import tarfile

SERVER_HOST = "your-ecs-public-ip"
SERVER_USER = "root"
SERVER_PASSWORD = "BRUe4zB%rR"

LOCAL_BACKEND_PATH = "/Users/tigerwen/workspace/nok_ailab/NOK_Nexus"
LOCAL_FRONTEND_PATH = "/Users/tigerwen/workspace/nok_ailab/NOK_Nexus_Web"
REMOTE_BASE_PATH = "/root/nok_app"


def create_tar_buffer(source_path):
    exclude_dirs = ['node_modules', '.next', '.git', '__pycache__', '.venv', 'logs', '.claude', 'dist']
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        for root, dirs, files in os.walk(source_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file.startswith('.'):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_path)
                tar.add(file_path, arcname=arcname)
    buffer.seek(0)
    return buffer


def ssh_connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, port=22, look_for_keys=False, allow_agent=False)
    return client


def run_command(client, command, timeout=300):
    print(f"  > {command[:100]}...")
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    if output:
        print(output[:2000])
    if error and exit_status != 0:
        print(f"  错误：{error[:500]}")
    return exit_status == 0, output, error


def main():
    print("=" * 60)
    print("CentOS 7 部署 - 安装 Docker")
    print("=" * 60)

    client = ssh_connect()
    print("连接成功!")

    try:
        # 1. 卸载旧版本
        print("\n===== 1. 清理旧版本 =====")
        run_command(client, "yum remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine", timeout=120)

        # 2. 安装 yum 工具
        print("\n===== 2. 安装 yum 工具 =====")
        run_command(client, "yum install -y yum-utils", timeout=120)

        # 3. 添加 Docker 仓库
        print("\n===== 3. 添加 Docker 仓库 =====")
        run_command(client, "yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo", timeout=120)

        # 4. 安装 Docker
        print("\n===== 4. 安装 Docker =====")
        run_command(client, "yum install -y docker-ce docker-ce-cli containerd.io", timeout=300)

        # 5. 启动 Docker
        print("\n===== 5. 启动 Docker =====")
        run_command(client, "systemctl start docker")
        run_command(client, "systemctl enable docker")

        # 6. 安装 Docker Compose
        print("\n===== 6. 安装 Docker Compose =====")
        run_command(client, "curl -L https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose", timeout=120)
        run_command(client, "chmod +x /usr/local/bin/docker-compose")

        # 7. 验证
        print("\n===== 7. 验证安装 =====")
        run_command(client, "docker --version")
        run_command(client, "docker-compose --version")

        # 8. 上传代码
        print("\n===== 8. 上传代码 =====")
        run_command(client, f"mkdir -p {REMOTE_BASE_PATH}")

        # 上传后端
        print("  上传后端...")
        tar_buffer = create_tar_buffer(LOCAL_BACKEND_PATH)
        with client.open_sftp() as sftp:
            sftp.putfo(tar_buffer, "/tmp/backend.tar.gz")
        run_command(client, f"tar -xzf /tmp/backend.tar.gz -C {REMOTE_BASE_PATH}/backend")

        # 上传前端
        print("  上传前端...")
        tar_buffer = create_tar_buffer(LOCAL_FRONTEND_PATH)
        with client.open_sftp() as sftp:
            sftp.putfo(tar_buffer, "/tmp/frontend.tar.gz")
        run_command(client, f"tar -xzf /tmp/frontend.tar.gz -C {REMOTE_BASE_PATH}/frontend")

        run_command(client, "rm /tmp/backend.tar.gz /tmp/frontend.tar.gz")

        # 9. 创建配置文件
        print("\n===== 9. 创建配置文件 =====")

        # 后端 .env
        backend_env = """# 应用基础配置
APP_NAME=企业 AI 平台
APP_VERSION=1.0.0
DEBUG=False
API_PREFIX=/api/v1

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 数据库配置
DB_HOST=your-rds-host.rds.aliyuncs.com
DB_PORT=5432
DB_NAME=nok_ailab
DB_USER=nok_normal
DB_PASSWORD=your-rds-password
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# JWT 配置
JWT_SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12

# CORS 配置
CORS_ORIGINS=["http://your-ecs-public-ip:3000","http://your-ecs-public-ip"]

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
"""
        with client.open_sftp() as sftp:
            sftp.putfo(io.BytesIO(backend_env.encode()), f"{REMOTE_BASE_PATH}/backend/.env")

        # 前端 .env.local
        frontend_env = "NEXT_PUBLIC_API_BASE_URL=http://your-ecs-public-ip:8000\n"
        with client.open_sftp() as sftp:
            sftp.putfo(io.BytesIO(frontend_env.encode()), f"{REMOTE_BASE_PATH}/frontend/.env.local")

        # docker-compose.yml
        docker_compose = """version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: nok_backend
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - ./backend/logs:/app/logs
    networks:
      - nok_network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: nok_frontend
    restart: always
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - nok_network

networks:
  nok_network:
    driver: bridge
"""
        with client.open_sftp() as sftp:
            sftp.putfo(io.BytesIO(docker_compose.encode()), f"{REMOTE_BASE_PATH}/docker-compose.yml")

        print("配置文件创建完成!")

        # 10. 构建并启动
        print("\n===== 10. 构建并启动服务 =====")
        run_command(client, f"cd {REMOTE_BASE_PATH} && docker-compose up -d --build", timeout=600)

        # 11. 查看状态
        print("\n===== 11. 查看状态 =====")
        run_command(client, f"cd {REMOTE_BASE_PATH} && docker-compose ps")

        print("\n" + "=" * 60)
        print("✅ 部署完成!")
        print(f"  后端 API: http://{SERVER_HOST}:8000")
        print(f"  前端网页：http://{SERVER_HOST}:3000")
        print("\n管理命令:")
        print(f"  cd {REMOTE_BASE_PATH}")
        print("  docker-compose ps       # 查看状态")
        print("  docker-compose logs     # 查看日志")
        print("  docker-compose restart  # 重启服务")
        print("=" * 60)

    except Exception as e:
        print(f"\n部署出错：{e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
