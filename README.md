# NodeHarbor - 代理节点与客户端管理平台

<div align="center">

![NodeHarbor Logo](./frontend/public/favicon.svg)

### 现代化代理订阅配置分发 & 客户端聚合下载平台

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/Vue-3.4+-4FC08D?style=flat&logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![Vite](https://img.shields.io/badge/Vite-5.0+-646CFF?style=flat&logo=vite&logoColor=white)](https://vitejs.dev)
[![Element Plus](https://img.shields.io/badge/Element%20Plus-2.6+-409EFF?style=flat&logo=elementplus&logoColor=white)](https://element-plus.org)
[![CodeMirror 6](https://img.shields.io/badge/CodeMirror-6.0+-d83b01?style=flat)](https://codemirror.net)
[![SQLite](https://img.shields.io/badge/SQLite-3.0+-003B57?style=flat&logo=sqlite&logoColor=white)](https://www.sqlite.org)

</div>

---

## 📖 项目简介

**NodeHarbor** 是一个轻量、高效且美观的代理节点订阅管理与多平台客户端中转下载平台。基于 **FastAPI + Vue 3** 全栈架构开发，提供代理订阅管理、定时自动同步、免登录订阅分发、多平台客户端 GitHub Release 加速下载以及完善的权限隔离体系。

---

## ✨ 核心特性

- 🔐 **角色与权限隔离**
  - 基于 JWT Token 认证，内置管理员 (`admin`) 与普通用户 (`user`) 双角色。
  - 管理员享有配置全生命周期管理、可见性控制、定时任务设置、在线编辑、系统监控及缓存清理权限；
  - 普通用户专注浏览与下载可用配置、复制免登录订阅直链以及客户端下载。

- 📄 **多渠道配置导入与在线编辑**
  - **本地上传**：支持拖拽上传 `.yaml` / `.yml` 格式代理配置文件；
  - **URL 订阅导入**：输入外部订阅链接一键拉取并自动解析；
  - **YAML 文本粘贴**：直接粘贴配置文本快速生成；
  - **在线代码高亮编辑**：内置 CodeMirror 6 编辑器，支持 YAML 语法高亮、快捷键保存与撤销。

- 🔄 **定时自动更新与手动同步**
  - 支持为订阅源配置自动更新策略：**每日指定时间 (Daily)** 或 **固定间隔小时 (Interval)** 自动拉取；
  - 后台异步轮询调度，保证配置数据常新；
  - 管理员支持一键手动立即同步更新。

- 👁️ **细粒度可见性控制**
  - 管理员可一键切换配置公开状态 (`is_public`)，随时隐藏维护中或内部专属节点配置。

- 🔗 **标准免登录订阅链接分发**
  - 提供标准的公开订阅链接 (`/api/configs/{id}/download`)，附带 `profile-update-interval` 等标准头；
  - 完美兼容 Clash、Clash Verge、Clash.Meta、Shadowrocket、Sing-box 等主流客户端直接拉取订阅。

- 📦 **多平台代理客户端聚合中转**
  - 支持 **v2rayN** (Windows)、**Clash Verge Rev** (全平台)、**v2rayNG** (Android)、**Clash Meta for Android** (Android) 4 大主流客户端；
  - **24 小时 Release 元数据本地缓存**：避免频繁请求 GitHub API 导致限流；
  - **服务端流式中转下载与进度监听**：解决国内访问 GitHub Release 速度慢或无法直连的问题；
  - **客户端二进制缓存自动淘汰**：单文件 1 小时自动清理，总缓存容量上限 512MB 限制，并支持管理员一键清空。

- 👥 **用户账号与权限管理**
  - **用户全生命周期管理**：管理员专属可视化用户管理大厅，支持查询系统中所有用户列表与状态；
  - **密码与角色修改**：管理员可直接修改任意用户（包括普通用户和管理员自身）的登录密码，支持分配/调整角色；
  - **便捷新增用户**：支持快速添加新账号，内置一键生成 12 位强随机密码与明文切换；
  - **关键安全防护**：防误删当前登录账号、防删除/降级系统中唯一的管理员，避免系统失控。

- 📊 **可视化管理仪表盘**
  - **全局状态监控**：直观展示系统配置总数、注册用户数、客户端缓存数及存储占用情况；
  - **快捷操作入口**：提供上传配置、用户管理、客户端清理等高频操作的一键跳转；
  - **动态响应设计**：针对桌面端与移动端优化，提供紧凑指标网格与流式触控体验。

- 📱 **全平台自适应响应式设计**
  - 专为移动端优化的底部快捷导航栏与卡片交互；
  - 桌面端毛玻璃拟态质感

---

## 🛠️ 技术栈

| 模块 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **后端框架** | FastAPI (Python 3.10+) | 高性能异步 API 框架 |
| **数据库 & ORM** | SQLite + SQLAlchemy 2.0 | 轻量嵌入式数据库与 ORM 映射 |
| **认证安全** | Python-Jose + Passlib (Bcrypt) | JWT 鉴权与密码哈希加密 |
| **前端框架** | Vue 3 (Composition API) + Vite | 现代化高效前端工程 |
| **UI 组件库** | Element Plus + @element-plus/icons-vue | 优雅的深色拟态定制 UI |
| **代码编辑器** | CodeMirror 6 (@codemirror/lang-yaml) | 高性能 YAML 在线编辑器 |
| **状态管理 & 路由** | Pinia + Vue Router | 响应式状态流与路由权限守卫 |
| **网络请求** | Axios / aiohttp / aiofiles | 异步 HTTP 请求与大文件流式传输 |

---

## 🚀 快速开始

### 1. 一键脚本启停（推荐）

项目根目录提供了完善的自动化 Shell 管理脚本，内置 Python 虚拟环境检测、前后端依赖自动安装、进程健康检查与端口冲突处理。

```bash
# 赋予执行权限
chmod +x start.sh stop.sh

# 一键启动（后台启动 FastAPI 后端 8001 与 Vite 前端 5173）
./start.sh

# 一键停止（安全终止进程并清理端口占用）
./stop.sh
```

### 2. 手动分步启动

#### 后端启动 (Backend)
```bash
cd backend

# 创建并激活虚拟环境 (规范推荐)
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动 FastAPI 服务 (默认监听 8001 端口)
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### 前端启动 (Frontend)
```bash
cd frontend

# 安装 Node 依赖
npm install

# 启动 Vite 开发服务器 (默认监听 5173 端口)
npm run dev
```

---

## 🔑 默认账号信息

系统首次启动时会自动初始化 SQLite 数据库并创建默认账号：

| 账号类型 | 用户名 | 默认密码 | 权限范围 |
| :--- | :--- | :--- | :--- |
| **管理员 (Admin)** | `admin` | `admin` | 全局配置增删改查、在线编辑、导入与同步设置、客户端缓存管理、系统状态监控 |
| **普通用户 (User)** | `user` | `user` | 查看与下载公开代理配置、复制免登录订阅直链、客户端中转下载 |

> 统一登录入口：访问前端根路径（例如 `http://localhost:5173/login` 或实际部署域名）。

---

## 📁 项目目录结构

详细的项目文件与模块架构索引请参阅 [index.md](./index.md)。

---

## 📄 开源许可证

本项目基于 [GPL-3.0 License](./LICENSE) 开源协议。
