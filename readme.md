# Profile Manager

一个使用 **FastAPI** + **Vue 3 (Vite)** 的简单后台，用于管理用户余额和 AI Key。

## 后端 (FastAPI)

```bash
cd backend
python -m venv .venv && source .\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

默认监听 `http://localhost:8000`，包含健康检查、用户、余额、API Key 的 CRUD 接口。

## 前端 (Vue 3)

```bash
cd frontend
npm install
npm run dev
```

前端默认走 `http://localhost:8000`，如需自定义后端地址可设置 `VITE_API_BASE` 环境变量。

## 主要特性

- 用户创建、余额累计增减，防止负数。
- API Key 的创建、删除，支持绑定用户。
- 概览卡片汇总用户数量、Key 数量和余额总额。
- CORS 已启用，可直接在浏览器本地调试。
