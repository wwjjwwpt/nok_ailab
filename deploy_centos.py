#!/usr/bin/env python3
"""
NOK_Nexus 项目部署脚本 - CentOS/RHEL 版本
"""
import paramiko
import os
import io
import tarfile

# 服务器配置
SERVER_HOST = "your-ecs-public-ip"
SERVER_USER = "root"
SERVER_PASSWORD = "BRUe4zB%rR"

# 本地项目路径
LOCAL_BACKEND_PATH = "/Users/tigerwen/workspace/nok_ailab/NOK_Nexus"
LOCAL_FRONTEND_PATH = "/Users/tigerwen/workspace/nok_ailab/NOK_Nexus_Web"

# 远程部署路径
REMOTE_BASE_PATH = "/root/nok_app"
REMOTE_BACKEND_PATH = f"{REMOTE_BASE_PATH}/backend"
REMOTE_FRONTEND_PATH = f"{REMOTE_BASE_PATH}/frontend"


def create_tar_buffer(source_path, exclude_dirs=None):
    if exclude_dirs is None:
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
    client.connect(
        hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD,
        port=22, look_for_keys=False, allow_agent=False
    )
    return client


def run_command(client, command, timeout=300):
    print(f"  > {command}")
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    if output:
        print(output[:3000])
    if error and exit_status != 0:
        print(f"  错误：{error[:500]}")
    return exit_status == 0, output, error


def setup_server(client):
    """安装 CentOS 环境"""
    print("\n===== 1. 安装系统依赖 =====")

    # 安装 EPEL 和 IUS 源
    run_command(client, "yum install -y epel-release", timeout=120)

    # 安装 Python 3.11
    run_command(client, "yum install -y python311 python311-pip python311-devel", timeout=120)

    # 安装 Node.js 20
    run_command(client, "curl -fsSL https://rpm.nodesource.com/setup_20.x | bash -", timeout=120)
    run_command(client, "yum install -y nodejs", timeout=120)

    # 安装 PM2
    run_command(client, "npm install -g pm2", timeout=120)

    # 安装 git 和 gcc（编译依赖）
    run_command(client, "yum install -y git gcc", timeout=120)

    # 验证
    run_command(client, "python3.11 --version")
    run_command(client, "node --version")
    run_command(client, "npm --version")


def deploy_backend(client):
    """部署后端"""
    print("\n===== 2. 部署后端服务 =====")

    run_command(client, f"mkdir -p {REMOTE_BACKEND_PATH}/logs")

    # 上传代码
    print("  上传后端代码...")
    tar_buffer = create_tar_buffer(LOCAL_BACKEND_PATH)
    with client.open_sftp() as sftp:
        sftp.putfo(tar_buffer, "/tmp/backend.tar.gz")
    run_command(client, f"tar -xzf /tmp/backend.tar.gz -C {REMOTE_BACKEND_PATH}")
    run_command(client, "rm /tmp/backend.tar.gz")

    # 配置文件
    env_path = os.path.join(LOCAL_BACKEND_PATH, ".env")
    if os.path.exists(env_path):
        with open(env_path, 'rb') as f:
            with client.open_sftp() as sftp:
                sftp.putfo(f, f"{REMOTE_BACKEND_PATH}/.env")

    # 虚拟环境和依赖
    print("  创建 Python 3.11 虚拟环境...")
    run_command(client, f"cd {REMOTE_BACKEND_PATH} && python3.11 -m venv venv")
    print("  安装 Python 依赖...")
    run_command(client, f"cd {REMOTE_BACKEND_PATH} && ./venv/bin/pip install -r requirements.txt", timeout=600)


def deploy_frontend(client):
    """部署前端"""
    print("\n===== 3. 部署前端服务 =====")

    run_command(client, f"mkdir -p {REMOTE_FRONTEND_PATH}")

    # 上传代码
    print("  上传前端代码...")
    tar_buffer = create_tar_buffer(LOCAL_FRONTEND_PATH)
    with client.open_sftp() as sftp:
        sftp.putfo(tar_buffer, "/tmp/frontend.tar.gz")
    run_command(client, f"tar -xzf /tmp/frontend.tar.gz -C {REMOTE_FRONTEND_PATH}")
    run_command(client, "rm /tmp/frontend.tar.gz")

    # 更新配置
    frontend_env = "NEXT_PUBLIC_API_BASE_URL=http://your-ecs-public-ip:8000\n"
    with client.open_sftp() as sftp:
        sftp.putfo(io.BytesIO(frontend_env.encode()), f"{REMOTE_FRONTEND_PATH}/.env.local")

    # 安装并构建
    print("  安装 Node 依赖...")
    run_command(client, f"cd {REMOTE_FRONTEND_PATH} && npm install", timeout=600)
    print("  构建前端项目...")
    run_command(client, f"cd {REMOTE_FRONTEND_PATH} && npm run build", timeout=600)


def start_services(client):
    """启动服务"""
    print("\n===== 4. 启动服务 =====")

    # 停止旧进程
    run_command(client, "pm2 delete nok_backend 2>/dev/null || true")
    run_command(client, "pm2 delete nok_frontend 2>/dev/null || true")

    # 启动后端
    gunicorn_cmd = f"cd {REMOTE_BACKEND_PATH} && {REMOTE_BACKEND_PATH}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000"
    run_command(client, f"pm2 start '{gunicorn_cmd}' --name nok_backend")

    # 启动前端
    next_cmd = f"cd {REMOTE_FRONTEND_PATH} && npm start"
    run_command(client, f"pm2 start '{next_cmd}' --name nok_frontend")

    # 保存和自启
    run_command(client, "pm2 save")
    run_command(client, "pm2 startup systemd -u root --force")

    # 查看状态
    print("\n===== 服务状态 =====")
    run_command(client, "pm2 status")


def main():
    print("=" * 60)
    print("NOK_Nexus 部署脚本 (CentOS/RHEL)")
    print("=" * 60)

    print(f"\n连接到 {SERVER_HOST}...")
    try:
        client = ssh_connect()
        print("连接成功!")
    except Exception as e:
        print(f"连接失败：{e}")
        return

    try:
        setup_server(client)
        deploy_backend(client)
        deploy_frontend(client)
        start_services(client)

        print("\n" + "=" * 60)
        print("✅ 部署完成!")
        print(f"  后端 API: http://{SERVER_HOST}:8000")
        print(f"  前端网页：http://{SERVER_HOST}:3000")
        print("\n管理命令:")
        print("  pm2 status          # 查看状态")
        print("  pm2 logs            # 查看日志")
        print("  pm2 restart all     # 重启服务")
        print("=" * 60)

    except Exception as e:
        print(f"\n部署出错：{e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
