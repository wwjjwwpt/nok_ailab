# GitHub Actions 部署到阿里云 ECS

这套流水线会在推送 `main` 分支后，把当前仓库文件上传到 ECS，并在 ECS 上用 Docker Compose 重建前端和后端容器。

## 1. GitHub 仓库准备

在项目根目录初始化并推送仓库：

```bash
git init
git branch -M main
git add .
git commit -m "Initial deploy setup"
git remote add origin git@github.com:<your-user>/<your-repo>.git
git push -u origin main
```

推送前确认 `.env`、`.env.local`、`node_modules`、`venv`、`.next`、日志和压缩包没有被加入 git。

## 2. 阿里云 ECS 准备

ECS 安全组至少开放：

- `22`：GitHub Actions SSH 部署
- `80` / `443`：网站访问
- 如暂时不用 Nginx 反代，可临时开放 `3000` 和 `8000` 测试

推荐系统：Ubuntu 22.04 LTS。流水线会自动安装 Docker；如果你使用非 root 用户，需要该用户有 `sudo` 权限。

## 3. GitHub Secrets

在 GitHub 仓库进入 `Settings -> Secrets and variables -> Actions -> New repository secret`，添加：

| Secret | 示例 | 说明 |
| --- | --- | --- |
| `ECS_HOST` | `1.2.3.4` | ECS 公网 IP |
| `ECS_USER` | `root` | SSH 用户 |
| `ECS_PORT` | `22` | SSH 端口，可选 |
| `ECS_SSH_KEY` | `-----BEGIN OPENSSH PRIVATE KEY-----...` | 能登录 ECS 的私钥 |
| `DEPLOY_PATH` | `/opt/nok_ailab` | 部署目录，可选 |
| `APP_ENV` | 多行 `.env` 内容 | 后端生产环境变量 |
| `WEB_ENV` | 多行 `.env.local` 内容 | 前端生产环境变量 |

`APP_ENV` 示例：

```env
APP_NAME=企业 AI 平台
APP_VERSION=1.0.0
DEBUG=False
API_PREFIX=/api/v1
HOST=0.0.0.0
PORT=8000
DB_HOST=your-rds-host.rds.aliyuncs.com
DB_PORT=5432
DB_NAME=nok_ailab
DB_USER=postgres
DB_PASSWORD=your-rds-password
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your-redis-password
JWT_SECRET_KEY=replace-with-a-random-string-longer-than-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12
CORS_ORIGINS=["https://your-domain.com","http://your-ecs-public-ip:3000"]
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

`WEB_ENV` 示例：

```env
NEXT_PUBLIC_API_BASE_URL=https://your-domain.com
```

如果还没有域名，可以先用：

```env
NEXT_PUBLIC_API_BASE_URL=http://your-ecs-public-ip:8000
```

## 4. 触发部署

推送到 `main` 会自动部署；也可以在 GitHub `Actions -> Deploy to Aliyun ECS -> Run workflow` 手动触发。

ECS 上检查状态：

```bash
cd /opt/nok_ailab
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
```

本地开发如需同时启动 PostgreSQL 和 Redis：

```bash
docker compose --profile local up -d --build
```
