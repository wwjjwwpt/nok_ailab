# NOK_Nexus 项目部署流程总结

## 部署概览

将 Next.js + FastAPI 全栈应用部署到 CentOS 7 服务器的完整流程。

---

## 一、服务器环境信息

- **操作系统**: CentOS Linux 7 (Core)
- **Python**: 系统自带 Python 3.6.8（不满足项目需求）
- **Node.js**: 初始未安装
- **架构**: x86_64 (AMD64)

---

## 二、部署方案选择

### 方案对比

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| Docker 部署 | 环境隔离、版本一致、易管理 | 需要安装 Docker | ✅ 采用 |
| 直接部署 | 无需额外工具 | 依赖冲突、环境复杂 | ❌ 放弃 |
| 无服务器部署 | 免运维 | 成本高、定制性差 | ❌ 放弃 |

### 最终方案：Docker Compose

1. 使用 Docker 容器运行后端（Python 3.11 + FastAPI）
2. 使用 Docker 容器运行前端（Node 20 + Next.js）
3. 通过 Docker Compose 统一管理

---

## 三、完整部署流程

### 步骤 1: 安装 Docker

```bash
# 1. 安装 EPEL 源
yum install -y epel-release

# 2. 安装 yum 工具
yum install -y yum-utils

# 3. 添加 Docker 仓库（使用阿里云镜像）
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo -o /etc/yum.repos.d/docker-ce.repo

# 4. 安装 Docker
yum install -y docker-ce docker-ce-cli containerd.io

# 5. 启动 Docker
systemctl start docker
systemctl enable docker
```

### 步骤 2: 配置 Docker 镜像加速

```bash
# 配置阿里云镜像加速器
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://b9pmyelo2ap8sz4a.mirror.aliyuncs.com",
    "https://docker.m.daocloud.io"
  ]
}
EOF

# 修复 DNS（解决镜像拉取超时问题）
echo 'nameserver 8.8.8.8' > /etc/resolv.conf
echo 'nameserver 114.114.114.114' >> /etc/resolv.conf

# 重启 Docker
systemctl daemon-reload
systemctl restart docker

# 验证配置
docker info | grep -A 3 'Registry Mirrors'
```

### 步骤 3: 安装 Docker Compose

```bash
# 下载 Docker Compose
curl -L https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose

# 添加执行权限
chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

### 步骤 4: 上传项目代码

```bash
# 本地打包（排除 node_modules、.next 等）
cd /path/to/NOK_Nexus
tar -czf backend.tar.gz --exclude='node_modules' --exclude='.git' \
    --exclude='__pycache__' --exclude='.claude' --exclude='*.pyc' .

cd /path/to/NOK_Nexus_Web
tar -czf frontend.tar.gz --exclude='node_modules' --exclude='.next' \
    --exclude='.git' --exclude='.claude' .

# 上传到服务器
scp backend.tar.gz root@SERVER_IP:/tmp/
scp frontend.tar.gz root@SERVER_IP:/tmp/

# 服务器解压
mkdir -p /root/nok_app/backend
mkdir -p /root/nok_app/frontend

tar -xzf /tmp/backend.tar.gz -C /root/nok_app/backend
tar -xzf /tmp/frontend.tar.gz -C /root/nok_app/frontend
```

### 步骤 5: 创建配置文件

**后端 .env 文件** (`/root/nok_app/backend/.env`):
```bash
# 应用配置
APP_NAME=企业 AI 平台
APP_VERSION=1.0.0
DEBUG=False
API_PREFIX=/api/v1

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 数据库配置（阿里云 RDS）
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

# CORS 配置
CORS_ORIGINS=["http://your-ecs-public-ip:3000","http://your-ecs-public-ip"]
```

**前端 .env.local 文件** (`/root/nok_app/frontend/.env.local`):
```bash
NEXT_PUBLIC_API_BASE_URL=http://your-ecs-public-ip:8000
```

**docker-compose.yml 文件** (`/root/nok_app/docker-compose.yml`):
```yaml
version: '3.8'

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
    environment:
      - DB_HOST=your-rds-host.rds.aliyuncs.com
      - DB_PORT=5432
      - DB_NAME=nok_ailab
      - DB_USER=nok_normal
      - DB_PASSWORD=your-rds-password

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
```

### 步骤 6: 构建并启动

```bash
cd /root/nok_app

# 构建并启动（首次部署）
docker-compose up -d --build

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 单独查看某个服务日志
docker logs nok_backend --tail 50
docker logs nok_frontend --tail 50
```

---

## 四、关键问题与解决方案

### 问题 1: CentOS 7 系统版本过老

**问题描述**:
- 系统 glibc 版本为 2.17，无法安装 Node.js 20+
- Python 3.6.8 不满足 FastAPI 项目需求（需要 3.8+）

**解决方案**:
使用 Docker 容器化部署，绕过系统版本限制

---

### 问题 2: Docker 镜像拉取超时

**问题描述**:
```
failed to do request: Head "https://registry-1.docker.io/v2/library/python/manifests/3.11-slim": dial tcp: i/o timeout
```

**解决方案**:
1. 配置阿里云 Docker 镜像加速器
2. 修改 DNS 为 8.8.8.8 和 114.114.114.114

---

### 问题 3: SQLAlchemy 表重复定义

**问题描述**:
```
sqlalchemy.exc.InvalidRequestError: Table 'market_researches' is already defined for this MetaData instance.
```

**原因**:
`app/models/__init__.py` 和 `app/models/market_research.py` 都定义了 `MarketResearch` 类

**解决方案**:
删除 `__init__.py` 中的重复定义，保留独立模块中的定义

---

### 问题 4: Next.js 构建失败

**问题描述**:
```
Type error: Cannot find name 'get'.
```

**原因**:
`useAuth.ts` 中使用了未导入的 `get()` 函数

**解决方案**:
使用 Zustand store 的 `getState()` 方法：
```typescript
// 错误写法
if (get().menus.length === 0) { ... }

// 正确写法
const menuStore = useMenuStore.getState();
if (menuStore.menus.length === 0) { ... }
```

---

### 问题 5: 前端构建成功但无法访问后端

**问题描述**:
前端页面能打开，但 API 请求失败

**原因**:
前端 `.env.local` 配置的是 `http://localhost:8000`

**解决方案**:
更新为服务器公网 IP：
```bash
NEXT_PUBLIC_API_BASE_URL=http://your-ecs-public-ip:8000
```

然后重新构建前端：
```bash
docker-compose build frontend
docker-compose restart frontend
```

---

## 五、运维管理命令

### 服务管理

```bash
cd /root/nok_app

# 查看状态
docker-compose ps

# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart backend
docker-compose restart frontend

# 重新构建并启动
docker-compose up -d --build
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看后端日志
docker logs nok_backend --tail 100 -f

# 查看前端日志
docker logs nok_frontend --tail 100 -f

# 查看最近 1 小时日志
docker logs --since 1h nok_backend
```

### 容器管理

```bash
# 进入容器
docker exec -it nok_backend bash
docker exec -it nok_frontend sh

# 查看容器资源占用
docker stats

# 清理未使用的资源
docker system prune -a
```

---

## 六、Dockerfile 优化

### 后端 Dockerfile 优化

```dockerfile
# 多阶段构建 - 后端
FROM python:3.11-slim as backend-builder

WORKDIR /app

# 使用国内 pip 镜像
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY . .

# 运行镜像
FROM python:3.11-slim

WORKDIR /app

# 使用国内 pip 镜像
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin
COPY . .

# 创建日志目录
RUN mkdir -p logs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 前端 Dockerfile 优化

```dockerfile
# 多阶段构建 - 前端
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# 使用国内 npm 镜像
RUN npm config set registry https://registry.npmmirror.com

# 复制 package 文件
COPY package.json ./

# 安装依赖
RUN npm install --frozen-lockfile

# 复制源码
COPY . .

# 构建生产版本
RUN npm run build

# 生产镜像
FROM node:20-alpine

WORKDIR /app

# 使用国内 npm 镜像
RUN npm config set registry https://registry.npmmirror.com

COPY package.json ./
RUN npm install --production --frozen-lockfile

# 复制构建产物
COPY --from=frontend-builder /app/.next ./.next
COPY --from=frontend-builder /app/public ./public
COPY --from=frontend-builder /app/next.config.ts ./

EXPOSE 3000

ENV NODE_ENV=production

CMD ["npm", "start"]
```

---

## 七、自动化部署脚本

### deploy.py (本地执行)

```python
#!/usr/bin/env python3
"""
NOK_Nexus 自动化部署脚本
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
LOCAL_BACKEND_PATH = "/path/to/NOK_Nexus"
LOCAL_FRONTEND_PATH = "/path/to/NOK_Nexus_Web"

# 远程部署路径
REMOTE_BASE_PATH = "/root/nok_app"


def create_tar_buffer(source_path, exclude_dirs=None):
    """创建 tar.gz 字节流"""
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
        print(output[:2000])
    if error and exit_status != 0:
        print(f"错误：{error[:500]}")
    return exit_status == 0


def main():
    print("开始部署...")
    client = ssh_connect()

    try:
        # 创建目录
        run_command(client, f"mkdir -p {REMOTE_BASE_PATH}/backend")
        run_command(client, f"mkdir -p {REMOTE_BASE_PATH}/frontend")

        # 上传后端
        tar_buffer = create_tar_buffer(LOCAL_BACKEND_PATH)
        with client.open_sftp() as sftp:
            sftp.putfo(tar_buffer, "/tmp/backend.tar.gz")
        run_command(client, f"tar -xzf /tmp/backend.tar.gz -C {REMOTE_BASE_PATH}/backend")

        # 上传前端
        tar_buffer = create_tar_buffer(LOCAL_FRONTEND_PATH)
        with client.open_sftp() as sftp:
            sftp.putfo(tar_buffer, "/tmp/frontend.tar.gz")
        run_command(client, f"tar -xzf /tmp/frontend.tar.gz -C {REMOTE_BASE_PATH}/frontend")

        # 清理
        run_command(client, "rm /tmp/backend.tar.gz /tmp/frontend.tar.gz")

        # 构建并启动
        run_command(client, f"cd {REMOTE_BASE_PATH} && docker-compose up -d --build", timeout=600)

        print("部署完成!")

    finally:
        client.close()


if __name__ == "__main__":
    main()
```

---

## 八、检查清单

### 部署前检查

- [ ] 服务器 SSH 可访问
- [ ] 服务器磁盘空间充足 (`df -h`)
- [ ] 服务器内存充足 (`free -h`)
- [ ] 本地代码已提交 Git
- [ ] 敏感配置已从代码中移除

### 部署后检查

- [ ] Docker 容器正常运行 (`docker-compose ps`)
- [ ] 后端 API 可访问 (`curl http://SERVER_IP:8000/docs`)
- [ ] 前端页面可访问 (`curl http://SERVER_IP:3000`)
- [ ] 数据库连接正常
- [ ] 日志无错误信息

---

## 九、常用阿里云服务配置

### RDS PostgreSQL 连接

```bash
# 获取 RDS 连接信息
1. 登录阿里云控制台
2. 进入 RDS 管理控制台
3. 选择实例 -> 基本信息
4. 复制「内网地址」或「外网地址」

# 注意事项
- 内网地址：仅同地域 ECS 可访问
- 外网地址：任何网络可访问（需配置白名单）
- 白名单：添加服务器 IP 到 RDS 白名单
```

### 安全组配置

```bash
# 开放端口
1. 登录阿里云控制台
2. 进入 ECS -> 安全组
3. 添加入方向规则：
   - 端口 8000 (后端 API)
   - 端口 3000 (前端网页)
   - 协议：TCP
   - 授权对象：0.0.0.0/0 (或指定 IP)
```

---

## 十、故障排查指南

### 后端无法启动

```bash
# 1. 查看日志
docker logs nok_backend

# 2. 进入容器检查
docker exec -it nok_backend bash
cd /app && python -c "from app.main import app; print('OK')"

# 3. 检查数据库连接
docker exec -it nok_backend bash
psql -h DB_HOST -U DB_USER -d DB_NAME
```

### 前端无法访问

```bash
# 1. 查看日志
docker logs nok_frontend

# 2. 检查配置
docker exec -it nok_frontend sh
cat /app/.env.local

# 3. 测试 API 连通性
docker exec -it nok_frontend sh
curl http://backend:8000/docs
```

### 内存不足

```bash
# 查看内存使用
free -h
docker stats

# 清理未使用资源
docker system prune -a

# 增加 Swap（临时方案）
dd if=/dev/zero of=/swapfile bs=1G count=2
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

---

## 总结

本次部署成功将 Next.js + FastAPI 全栈应用部署到 CentOS 7 服务器，关键要点：

1. **使用 Docker 绕过系统版本限制**
2. **配置国内镜像加速解决网络问题**
3. **多阶段构建减小镜像体积**
4. **Docker Compose 统一管理多服务**
5. **自动化脚本提高部署效率**

---

*最后更新：2026-03-31*
