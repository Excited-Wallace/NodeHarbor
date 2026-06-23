# NodeHarbor - 代理节点管理平台

代理节点管理平台，提供代理订阅配置文件的管理、分发和主流代理客户端的中转下载服务。

## 技术栈

- **后端**: Python FastAPI + SQLite + SQLAlchemy
- **前端**: Vue 3 + Vite + Element Plus + CodeMirror 6
- **认证**: JWT Token

## 功能特性

- 🔐 管理员/用户双角色（仅密码认证，通过访问路径区分）
- 📄 代理订阅配置文件上传、在线编辑、下载
- 🔗 一键复制订阅链接，导入代理客户端
- 📦 代理客户端中转下载（V2Ray、Clash Verge、V2RayNG、Clash Meta）
- ⏱️ 客户端文件自动缓存，1小时过期清理

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 默认账号

- 管理员密码: `admin`（访问 `/admin/login`）
- 用户密码: `admin`（访问 `/login`）

## 项目结构

详见 [index.md](./index.md)
