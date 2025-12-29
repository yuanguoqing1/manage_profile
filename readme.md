# Profile Manager

一个使用 **FastAPI** + **Vue 3 (Vite)** 的现代化用户管理和 AI 配置平台。

## ✨ 主要特性

- 👤 **用户管理**：用户创建、余额管理、角色权限控制
- 🤖 **AI 模型配置**：支持多模型配置，API Key 管理
- 💬 **实时聊天**：WebSocket 实时通信，站内消息系统
- 🔐 **安全认证**：Token 认证，Redis 会话管理，密码强度验证
- 📊 **数据可视化**：仪表盘、统计图表、在线状态监控
- 🌐 **网页收藏**：分类管理，凭证存储

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 16+
- MySQL 5.7+ 或 8.0+
- Redis 5.0+

### 后端 (FastAPI)

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.\.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制并修改）
cp .env.example .env

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

默认监听 `http://localhost:8001`

### 前端 (Vue 3)

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量（可选）
cp .env.example .env

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

默认监听 `http://localhost:5173`

## 🔧 配置说明

### 后端环境变量

创建 `backend/.env` 文件：

```bash
# CORS 配置（生产环境必须设置）
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Token 过期时间（天）
TOKEN_EXPIRES_DAYS=7

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# MySQL 配置
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DB=manage_profile
```

### 前端环境变量

创建 `frontend/.env` 文件：

```bash
# 后端 API 地址
VITE_API_BASE=http://127.0.0.1:8001
```

## 📚 API 文档

启动后端服务后，访问：

- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## 🏗️ 项目结构

```
.
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API 路由
│   │   │   ├── middleware/ # 中间件（限流等）
│   │   │   └── routes/     # 端点实现
│   │   ├── core/           # 核心配置
│   │   ├── crud/           # 数据库操作
│   │   ├── db/             # 数据库配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # API 模型
│   │   └── services/       # 业务逻辑
│   └── requirements.txt
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/    # Vue 组件
│   │   ├── utils/         # 工具函数
│   │   ├── views/         # 页面组件
│   │   └── App.vue        # 根组件
│   └── package.json
└── IMPROVEMENTS.md        # 改进记录

```

## 🔒 安全特性

- ✅ **密码加密**：PBKDF2-HMAC-SHA256，60万次迭代
- ✅ **密码强度验证**：必须包含大小写字母和数字
- ✅ **API 限流**：防止暴力攻击和滥用
- ✅ **CORS 保护**：可配置的跨域策略
- ✅ **XSS 防护**：前端使用 DOMPurify 清理 HTML
- ✅ **Token 认证**：JWT 风格的 Token，支持过期时间

## 📈 性能优化

- ✅ **数据库索引**：关键字段已添加索引
- ✅ **连接池**：配置了数据库连接池
- ✅ **分页支持**：大数据量查询支持分页
- ✅ **Redis 缓存**：在线统计使用 Redis
- ✅ **防抖/节流**：前端搜索等操作已优化

## 🧪 测试

### 测试密码验证

```bash
# 应该失败（密码太短）
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"test","password":"short"}'

# 应该成功
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"test","password":"Password123"}'
```

### 测试限流

```bash
# 快速发送多个请求，超过限制后会返回 429
for i in {1..150}; do
  curl http://localhost:8001/health
done
```

## 📝 开发指南

### 代码规范

- 后端：使用 type hints，遵循 PEP 8
- 前端：使用 ES6+，组件化开发
- 提交：使用语义化提交信息

### 添加新功能

1. 后端：在 `backend/app/api/routes/` 添加路由
2. 前端：在 `frontend/src/components/` 或 `views/` 添加组件
3. 更新文档：修改 README 和 API 文档

## 🐛 常见问题

### 1. Redis 连接失败

如果 Redis 不可用，系统会自动降级使用数据库统计。检查 Redis 是否启动：

```bash
redis-cli ping
```

### 2. 数据库连接失败

检查 MySQL 是否启动，以及 `.env` 中的配置是否正确：

```bash
mysql -u root -p
```

### 3. CORS 错误

生产环境必须设置 `ALLOWED_ORIGINS` 环境变量：

```bash
export ALLOWED_ORIGINS=https://yourdomain.com
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题，请提交 Issue。

---

**最后更新**: 2025-12-29  
**版本**: 0.2.0
