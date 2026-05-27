#!/usr/bin/env python3
"""
在服务器上配置 Docker 镜像加速器
"""
import paramiko

SERVER_HOST = "your-ecs-public-ip"
SERVER_USER = "root"
SERVER_PASSWORD = "BRUe4zB%rR"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, port=22, look_for_keys=False, allow_agent=False)

# 修复 DNS
stdin, stdout, stderr = client.exec_command("""
echo 'nameserver 8.8.8.8' > /etc/resolv.conf
echo 'nameserver 114.114.114.114' >> /etc/resolv.conf
cat /etc/resolv.conf
""")
print("DNS 配置:")
print(stdout.read().decode())

# 配置 Docker daemon
docker_config = '''{
  "registry-mirrors": [
    "https://b9pmyelo2ap8sz4a.mirror.aliyuncs.com",
    "https://docker.m.daocloud.io"
  ]
}'''

stdin, stdout, stderr = client.exec_command(f"echo '{docker_config}' > /etc/docker/daemon.json")
print("Docker 配置:")
print(stdout.read().decode())

# 重启 Docker
stdin, stdout, stderr = client.exec_command("systemctl daemon-reload && systemctl restart docker")
print("Docker 重启完成")

# 验证
stdin, stdout, stderr = client.exec_command("docker info | grep -A 5 'Registry Mirrors'")
print("镜像加速器配置:")
print(stdout.read().decode())

client.close()
