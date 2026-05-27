#!/usr/bin/env python3
"""
使用 paramiko 部署 NOK_Nexus 项目到远程服务器
"""
import paramiko
import os
import tarfile
import io

# 服务器配置
SERVER_HOST = "your-ecs-public-ip"
SERVER_USER = "root"
SERVER_PASSWORD = "BRUe4zB%rR"

# 本地项目路径
LOCAL_BACKEND_PATH = "/Users/tigerwen/workspace/nok_ailab/NOK_Nexus"
LOCAL_FRONTEND_PATH = "/Users/tigerwen/workspace/nok_ailab/NOK_Nexus_Web"

# 远程部署路径
REMOTE_BASE_PATH = "/root/nok_deployment"
REMOTE_BACKEND_PATH = f"{REMOTE_BASE_PATH}/NOK_Nexus"
REMOTE_FRONTEND_PATH = f"{REMOTE_BASE_PATH}/NOK_Nexus_Web"


def create_tar_buffer(source_path, exclude_dirs=None):
    """创建 tar .gz 字节流"""
    if exclude_dirs is None:
        exclude_dirs = ['node_modules', '.next', '.git', '__pycache__', '.venv', 'logs', '.claude']

    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        for root, dirs, files in os.walk(source_path):
            # 排除指定目录
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
    """建立 SSH 连接"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=SERVER_HOST,
        username=SERVER_USER,
        password=SERVER_PASSWORD,
        port=22,
        look_for_keys=False,
        allow_agent=False
    )
    return client


def run_command(client, command, timeout=300):
    """运行远程命令"""
    print(f"执行：{command}")
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)

    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')

    if output:
        print(output)
    if error:
        print(f"错误：{error}")

    return exit_status == 0, output, error


def deploy_backend(client):
    """部署后端"""
    print("\n===== 部署后端 =====")

    # 创建 tar 包
    print("压缩后端代码...")
    tar_buffer = create_tar_buffer(LOCAL_BACKEND_PATH)

    # 创建远程目录
    run_command(client, f"mkdir -p {REMOTE_BACKEND_PATH}")

    # 上传 tar 包
    print("上传后端代码...")
    with client.open_sftp() as sftp:
        sftp.putfo(tar_buffer, f"/tmp/backend.tar.gz")

    # 解压
    print("解压后端代码...")
    run_command(client, f"tar -xzf /tmp/backend.tar.gz -C {REMOTE_BACKEND_PATH}")
    run_command(client, "rm /tmp/backend.tar.gz")

    # 复制 .env 文件
    env_path = os.path.join(LOCAL_BACKEND_PATH, ".env")
    if os.path.exists(env_path):
        print("上传后端配置文件...")
        with open(env_path, 'rb') as f:
            with client.open_sftp() as sftp:
                sftp.putfo(f, f"{REMOTE_BACKEND_PATH}/.env")

    print("后端部署完成!")


def deploy_frontend(client):
    """部署前端"""
    print("\n===== 部署前端 =====")

    # 创建 tar 包
    print("压缩前端代码...")
    tar_buffer = create_tar_buffer(LOCAL_FRONTEND_PATH)

    # 创建远程目录
    run_command(client, f"mkdir -p {REMOTE_FRONTEND_PATH}")

    # 上传 tar 包
    print("上传前端代码...")
    with client.open_sftp() as sftp:
        sftp.putfo(tar_buffer, f"/tmp/frontend.tar.gz")

    # 解压
    print("解压前端代码...")
    run_command(client, f"tar -xzf /tmp/frontend.tar.gz -C {REMOTE_FRONTEND_PATH}")
    run_command(client, "rm /tmp/frontend.tar.gz")

    # 复制 .env.local 文件
    env_path = os.path.join(LOCAL_FRONTEND_PATH, ".env.local")
    if os.path.exists(env_path):
        print("上传前端配置文件...")
        with open(env_path, 'rb') as f:
            with client.open_sftp() as sftp:
                sftp.putfo(f, f"{REMOTE_FRONTEND_PATH}/.env.local")

    print("前端部署完成!")


def setup_docker_compose(client):
    """创建 docker-compose 配置"""
    print("\n===== 配置 Docker Compose =====")

    docker_compose_content = f"""version: '3.8'

services:
  backend:
    build:
      context: ./NOK_Nexus
      dockerfile: Dockerfile
    container_name: nok_backend
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=your-rds-host.rds.aliyuncs.com
      - DB_PORT=5432
      - DB_NAME=nok_ailab
      - DB_USER=nok_normal
      - DB_PASSWORD=your-rds-password
    volumes:
      - ./NOK_Nexus/logs:/app/logs
    networks:
      - nok_network

  frontend:
    build:
      context: ./NOK_Nexus_Web
      dockerfile: Dockerfile
    container_name: nok_frontend
    restart: always
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
    depends_on:
      - backend
    networks:
      - nok_network

networks:
  nok_network:
    driver: bridge
"""

    # 写入 docker-compose.yml
    with client.open_sftp() as sftp:
        sftp.putfo(io.BytesIO(docker_compose_content.encode()), f"{REMOTE_BASE_PATH}/docker-compose.yml")

    print("docker-compose.yml 创建完成!")


def start_services(client):
    """启动服务"""
    print("\n===== 启动服务 =====")

    # 进入部署目录
    run_command(client, f"cd {REMOTE_BASE_PATH}")

    # 构建并启动
    print("构建并启动 Docker 容器...")
    success, output, error = run_command(
        client,
        f"cd {REMOTE_BASE_PATH} && docker-compose up -d --build",
        timeout=600
    )

    if success:
        print("\n服务启动成功!")
    else:
        print(f"\n服务启动可能有问题，请检查:\n{error}")


def main():
    """主函数"""
    print("=" * 50)
    print("NOK_Nexus 项目部署脚本")
    print("=" * 50)

    # 检查 paramiko
    try:
        import paramiko
    except ImportError:
        print("请先安装 paramiko: pip install paramiko")
        return

    # 连接服务器
    print(f"\n正在连接到 {SERVER_HOST}...")
    try:
        client = ssh_connect()
        print("连接成功!")
    except Exception as e:
        print(f"连接失败：{e}")
        return

    try:
        # 检查 Docker
        success, _, _ = run_command(client, "docker --version")
        if not success:
            print("警告：服务器上可能未安装 Docker")

        # 部署后端
        deploy_backend(client)

        # 部署前端
        deploy_frontend(client)

        # 配置 docker-compose
        setup_docker_compose(client)

        # 询问是否启动服务
        print("\n是否立即启动服务？(y/n)")
        # 由于无法交互式输入，默认启动
        start_services(client)

        print("\n" + "=" * 50)
        print("部署完成!")
        print(f"后端地址：http://{SERVER_HOST}:8000")
        print(f"前端地址：http://{SERVER_HOST}:3000")
        print("=" * 50)

    finally:
        client.close()
        print("\nSSH 连接已关闭")


if __name__ == "__main__":
    main()
