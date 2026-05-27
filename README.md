# NOK AI Lab - 企业级 AI 平台

> 基于 Next.js 15 + FastAPI 的企业级权限管理系统

## 技术栈

### 后端
- **框架**: FastAPI 0.115
- **数据库**: PostgreSQL 16 (阿里云 RDS)
- **缓存**: Redis 7
- **ORM**: SQLAlchemy 2.0
- **认证**: JWT + OAuth2
- **权限**: RBAC + 数据权限

### 前端
- **框架**: Next.js 15 + React 19
- **语言**: TypeScript 5.7
- **UI**: shadcn/ui + TailwindCSS
- **状态管理**: Zustand
- **HTTP**: Axios

## 功能特性

- ✅ 用户管理 (CRUD + 状态管理)
- ✅ 角色管理 (RBAC 模型)
- ✅ 菜单权限 (动态导航)
- ✅ 功能权限 (按钮/API 级)
- ✅ 数据权限 (5 种范围)
- ✅ 部门管理 (树形架构)
- ✅ 登录/操作日志
- ✅ JWT 认证 + Token 刷新
- ✅ 邮箱/手机验证码

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 20+
- PostgreSQL 16+
- Redis 7+

### 1. 克隆项目
```bash
git clone <repo-url> nok_ailab
cd nok_ailab
```

### 2. 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填写数据库配置

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档

### 3. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local
# 编辑 .env.local 填写 API 地址

# 启动开发服务器
npm run dev
```

访问 http://localhost:3000

### 4. Docker 一键启动

```bash
# 本地开发 (使用 Docker Compose)
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 默认账号

- 用户名：`admin`
- 密码：`admin123`

## 项目结构

```
nok_ailab/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # 数据模型
│   │   ├── schemas/     # Pydantic Schema
│   │   ├── services/    # 业务逻辑
│   │   └── main.py      # 应用入口
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/            # 前端服务
│   ├── src/
│   │   ├── app/        # Next.js 路由
│   │   ├── components/ # React 组件
│   │   ├── hooks/      # 自定义 Hooks
│   │   ├── lib/        # 工具函数
│   │   ├── stores/     # Zustand 状态
│   │   └── types/      # TypeScript 类型
│   ├── package.json
│   └── Dockerfile
│
├── infra/              # 基础设施配置
│   └── nginx/
│       └── nginx.conf
│
├── docs/               # 文档
│   ├── 数据库 ER 图.md
│   └── 阿里云部署指南.md
│
└── docker-compose.yml  # Docker 编排
```

## 核心 API

### 认证相关
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/auth/logout` | POST | 用户登出 |
| `/api/v1/auth/refresh` | POST | 刷新 Token |
| `/api/v1/auth/me` | GET | 获取当前用户 |

### 用户管理
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/users` | GET | 用户列表 |
| `/api/v1/users` | POST | 创建用户 |
| `/api/v1/users/{id}` | PUT | 更新用户 |
| `/api/v1/users/{id}` | DELETE | 删除用户 |

### 角色管理
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/roles` | GET | 角色列表 |
| `/api/v1/roles` | POST | 创建角色 |
| `/api/v1/roles/{id}/permissions` | POST | 分配权限 |

### 菜单管理
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/menus/tree` | GET | 菜单树 (当前用户) |
| `/api/v1/menus` | GET | 所有菜单 |

## 权限模型

```
用户 → 角色 → 菜单权限
        ↓    功能权限
        ↓    数据权限

用户也可直接拥有权限 (特殊授权)
```

### 数据范围类型
1. **ALL** - 全部数据
2. **ORG_AND_CHILD** - 本部门及子部门
3. **ORG_SELF** - 本部门
4. **SELF** - 仅本人
5. **CUSTOM** - 自定义范围

## 部署

参考 [阿里云部署指南](docs/阿里云部署指南.md)

## 开发计划

- [ ] AI 对话模块
- [ ] 知识库管理 (RAG)
- [ ] Prompt 管理
- [ ] Token 用量统计
- [ ] 多模型支持

## License

MIT
