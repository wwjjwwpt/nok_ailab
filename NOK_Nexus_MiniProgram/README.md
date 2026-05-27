# NOK Nexus 微信小程序

> NOK Nexus 企业智能工作台的微信小程序版本 - 账号密码登录

## 项目结构

```
NOK_Nexus_MiniProgram/
├── api/                    # API 接口管理
│   └── index.js           # 所有 API 接口定义
├── images/                 # 图片资源
├── pages/                  # 页面
│   ├── login/             # 登录页
│   ├── dashboard/         # 工作台首页
│   └── profile/           # 个人中心
├── utils/                  # 工具函数
│   └── request.js         # HTTP 请求封装
├── app.js                  # 小程序入口
├── app.json                # 小程序配置
├── app.wxss                # 全局样式
├── project.config.json     # 项目配置
└── README.md               # 项目文档
```

## 快速开始

### 1. 启动后端服务

```bash
cd ../NOK_Nexus

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档

### 2. 打开微信小程序

1. 打开 **微信开发者工具**
2. 导入项目：选择 `NOK_Nexus_MiniProgram` 目录
3. 编译运行

### 3. 登录测试

默认管理员账号：
- **用户名**: `admin`
- **密码**: `admin123`

## 登录流程

```
用户打开小程序
    │
    ▼
检查本地存储 token
    │
    ├── 有 token ──→ 进入首页
    │
    └── 无 token ──→ 显示登录页
                        │
                        ▼
                  输入用户名密码
                        │
                        ▼
                  发送到后端验证
                        │
                    ┌───┴───┐
                    │       │
                  成功     失败
                    │       │
                    ▼       ▼
                保存 token  提示错误
                    │
                    ▼
                进入首页
```

## 登录状态保存

```javascript
// 登录成功后保存
wx.setStorageSync('token', token)
wx.setStorageSync('userInfo', user)
wx.setStorageSync('loginTime', Date.now())

// 页面检查登录状态
const token = wx.getStorageSync('token')
if (!token) {
  wx.reLaunch({ url: '/pages/login/index' })
}
```

## 后端 API

### 登录接口

```javascript
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

### 响应示例

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "nickname": "管理员",
    "avatar": null
  }
}
```

## 注意事项

1. **后端服务必须先启动**，小程序才能登录
2. **HTTPS 要求**：生产环境必须使用 HTTPS
3. **域名备案**：服务器域名需要完成 ICP 备案
4. **Token 过期处理**：401 响应时自动清除登录状态并跳转登录页

## 相关文档

- [微信小程序官方文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)
- [NOK Nexus 后端文档](../NOK_Nexus/README.md)

## License

MIT
