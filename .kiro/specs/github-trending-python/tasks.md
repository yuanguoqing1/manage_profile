# Implementation Plan: GitHub 热点 Python 项目汇总

## Overview

本实现计划将 GitHub 热点项目功能分解为后端服务、API 路由和前端组件三个主要部分，采用增量开发方式，确保每个步骤都可验证。

## Tasks

- [x] 1. 实现后端 GitHub Service
  - [x] 1.1 创建 TrendingProject 数据模型和 GitHub Service 基础结构
    - 创建 `backend/app/services/github_service.py`
    - 定义 `TrendingProject` Pydantic 模型
    - 实现 `_build_search_query()` 构建 GitHub 搜索查询
    - _Requirements: 1.1, 1.3_

  - [x] 1.2 实现 GitHub API 调用逻辑
    - 实现 `_fetch_from_github()` 异步函数
    - 使用 httpx 调用 GitHub Search API
    - 处理 API 响应并转换为 TrendingProject 列表
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 1.3 实现 Redis 缓存逻辑
    - 实现 `_get_cached_projects()` 从 Redis 读取缓存
    - 实现 `_cache_projects()` 将数据写入 Redis
    - 设置缓存 TTL 为 3600 秒
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 1.4 实现主函数 `get_trending_python_projects()`
    - 整合缓存检查和 API 调用逻辑
    - 实现错误处理和日志记录
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.3, 2.4_

  - [ ]* 1.5 编写属性测试：项目列表排序正确性
    - **Property 1: 项目列表排序正确性**
    - **Validates: Requirements 1.2**

  - [ ]* 1.6 编写属性测试：项目数据完整性
    - **Property 2: 项目数据完整性**
    - **Validates: Requirements 1.3, 3.3**

- [x] 2. 实现后端 API 路由
  - [x] 2.1 创建 GitHub 路由模块
    - 创建 `backend/app/api/routes/github.py`
    - 实现 `GET /api/github/trending` 端点
    - 调用 GitHub Service 获取数据
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 2.2 注册路由到主路由器
    - 在 `backend/app/api/router.py` 中添加 github 路由
    - _Requirements: 3.1_

  - [x] 2.3 实现错误处理
    - 处理服务异常并返回适当的 HTTP 状态码
    - _Requirements: 3.4, 1.4_

  - [ ]* 2.4 编写 API 端点单元测试
    - 测试成功响应格式
    - 测试错误响应格式
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Checkpoint - 后端功能验证
  - 确保所有后端测试通过
  - 手动测试 API 端点响应
  - 如有问题请询问用户

- [x] 4. 实现前端组件
  - [x] 4.1 创建 GitHub Trending 视图组件
    - 创建 `frontend/src/views/GithubTrendingView.vue`
    - 实现组件基础结构和数据状态
    - 实现 `onMounted` 自动加载数据
    - _Requirements: 4.1, 4.2_

  - [x] 4.2 实现项目卡片列表渲染
    - 渲染项目名称、描述、星标数、Fork 数
    - 实现项目链接（新标签页打开）
    - _Requirements: 4.3, 4.4_

  - [x] 4.3 实现加载状态和错误处理
    - 显示加载指示器
    - 显示错误提示和重试按钮
    - _Requirements: 4.5, 4.6_

  - [x] 4.4 实现刷新功能
    - 添加刷新按钮
    - 实现刷新逻辑和按钮状态控制
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 5. 添加前端路由
  - [x] 5.1 注册 GitHub Trending 路由
    - 在路由配置中添加 `/github-trending` 路由
    - _Requirements: 4.1_

  - [x] 5.2 添加导航入口
    - 在导航菜单中添加 GitHub 热点入口
    - _Requirements: 4.1_

- [x] 6. Final Checkpoint - 完整功能验证
  - 确保所有测试通过
  - 验证前后端集成正常
  - 如有问题请询问用户

## Notes

- 任务标记 `*` 为可选测试任务，可跳过以加快 MVP 开发
- 每个任务都引用了具体的需求条目以便追溯
- Checkpoint 任务用于阶段性验证
- 属性测试使用 `hypothesis` 库验证通用正确性属性
