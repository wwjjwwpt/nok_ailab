# 市场调研模块 - API 文档

## 概述

市场调研模块用于记录和管理部门内对市场商品的价格调研数据。每个用户只能查看和操作自己创建的调研记录。

## 数据模型

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | bigint | 自动 | 主键 ID |
| user_id | bigint | 自动 | 创建人 ID（所属用户） |
| city | varchar(100) | 是 | 调研城市 |
| manufacturer | varchar(200) | 是 | 厂商名称 |
| product_name | varchar(200) | 是 | 商品名称 |
| price | decimal(12,2) | 是 | 调研价格 |
| research_date | date | 否 | 调研日期（默认当天） |
| remark | text | 否 | 备注信息 |
| status | smallint | 自动 | 状态（0-删除 1-正常） |
| created_at | timestamp | 自动 | 创建时间 |
| updated_at | timestamp | 自动 | 更新时间 |
| created_by | bigint | 自动 | 创建人 |
| updated_by | bigint | 自动 | 更新人 |
| creator | string | 计算 | 创建人姓名（关联查询） |
| updater | string | 计算 | 更新人姓名（关联查询） |

## API 端点

所有请求需要在 Header 中携带 JWT Token：
```
Authorization: Bearer <your_access_token>
```

### 1. 获取调研列表

```http
GET /api/v1/market-research
```

**查询参数：**
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 10，最大 100）
- `city`: 城市筛选（可选）
- `manufacturer`: 厂商筛选（可选）

**响应示例：**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "city": "深圳",
      "manufacturer": "华为",
      "product_name": "Mate 60 Pro",
      "price": 6999.00,
      "research_date": "2026-03-28",
      "remark": "旗舰店调研",
      "status": 1,
      "created_at": "2026-03-28T16:16:47.457377",
      "updated_at": "2026-03-28T16:16:47.457377",
      "creator": "管理员",
      "updater": null
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "has_next": false
}
```

### 2. 获取调研详情

```http
GET /api/v1/market-research/{id}
```

**路径参数：**
- `id`: 调研记录 ID

**响应示例：**
```json
{
  "id": 1,
  "user_id": 1,
  "city": "深圳",
  "manufacturer": "华为",
  "product_name": "Mate 60 Pro",
  "price": 6999.00,
  "research_date": "2026-03-28",
  "remark": "旗舰店调研",
  "status": 1,
  "created_at": "2026-03-28T16:16:47.457377",
  "updated_at": "2026-03-28T16:16:47.457377",
  "creator": "管理员",
  "updater": null
}
```

### 3. 创建调研记录

```http
POST /api/v1/market-research
Content-Type: application/json
```

**请求体：**
```json
{
  "city": "深圳",
  "manufacturer": "华为",
  "product_name": "Mate 60 Pro",
  "price": 6999.00,
  "research_date": "2026-03-28",
  "remark": "旗舰店调研"
}
```

**响应示例：**
```json
{
  "id": 1,
  "user_id": 1,
  "city": "深圳",
  "manufacturer": "华为",
  "product_name": "Mate 60 Pro",
  "price": 6999.00,
  "research_date": "2026-03-28",
  "remark": "旗舰店调研",
  "status": 1,
  "created_at": "2026-03-28T16:16:47.457377",
  "updated_at": "2026-03-28T16:16:47.457377",
  "creator": "管理员",
  "updater": null
}
```

### 4. 更新调研记录

```http
PUT /api/v1/market-research/{id}
Content-Type: application/json
```

**路径参数：**
- `id`: 调研记录 ID

**请求体（所有字段可选）：**
```json
{
  "city": "深圳",
  "manufacturer": "华为",
  "product_name": "Mate 60 Pro",
  "price": 6499.00,
  "research_date": "2026-03-28",
  "remark": "价格调整 - 促销活动"
}
```

**说明：**
- 只需提供要更新的字段
- `updated_at` 和 `updated_by` 会自动更新

### 5. 删除调研记录

```http
DELETE /api/v1/market-research/{id}
```

**路径参数：**
- `id`: 调研记录 ID

**响应示例：**
```json
{
  "message": "删除成功"
}
```

**说明：**
- 采用软删除，仅将 `status` 设置为 0
- 数据仍保留在数据库中

## 权限控制

- 所有 API 都需要 JWT 认证
- 用户只能查看和操作自己创建的调研记录（通过 `user_id` 过滤）
- 无法访问其他用户创建的数据

## 错误响应

### 401 Unauthorized
```json
{
  "detail": "未授权访问"
}
```

### 404 Not Found
```json
{
  "detail": "调研记录不存在"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "price"],
      "msg": "确保这个值大于 0",
      "type": "greater_than"
    }
  ]
}
```

## 微信小程序集成

### API 地址配置

在 `app.js` 中配置后端 API 地址：
```javascript
globalData: {
  apiBaseUrl: 'http://127.0.0.1:8000/api/v1'
  // 生产环境改为：https://your-domain.com/api/v1
}
```

### 调用示例

```javascript
// 获取调研列表
const token = wx.getStorageSync('token')
wx.request({
  url: `${app.globalData.apiBaseUrl}/market-research`,
  method: 'GET',
  data: { page: 1, page_size: 10 },
  header: {
    'Authorization': `Bearer ${token}`
  },
  success: (res) => {
    console.log(res.data)
  }
})

// 创建调研
wx.request({
  url: `${app.globalData.apiBaseUrl}/market-research`,
  method: 'POST',
  data: {
    city: '深圳',
    manufacturer: '华为',
    product_name: 'Mate 60 Pro',
    price: 6999.00,
    research_date: '2026-03-28',
    remark: '旗舰店调研'
  },
  header: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
```

## 部署说明

### 数据库迁移

执行 SQL 脚本创建表：
```bash
python3 scripts/migrations/create_market_research_table.py
```

或直接在 psql 中执行：
```sql
-- 见 scripts/migrations/create_market_research_table.sql
```

### 启动后端服务

```bash
cd NOK_Nexus
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 测试 API

使用 Postman 或 curl 测试：
```bash
# 登录获取 token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 使用 token 访问 API
curl -X GET http://localhost:8000/api/v1/market-research \
  -H "Authorization: Bearer <your_token>"
```

## 更新日志

- 2026-03-28: 初始版本，实现完整 CRUD 功能
  - 数据库表设计
  - Model/Schema/路由实现
  - 权限控制（用户数据隔离）
  - 软删除功能
  - 审计字段自动填充
