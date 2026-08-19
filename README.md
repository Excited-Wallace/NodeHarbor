# NodeHarbor - 代理节点管理平台

代理节点管理平台，提供代理订阅配置文件的管理、分发和主流代理客户端的中转下载服务。

## 技术栈

- **后端**: Python FastAPI + SQLite + SQLAlchemy
- **前端**: Vue 3 + Vite + Element Plus + CodeMirror 6
- **认证**: JWT Token

## 功能特性

- 🔐 账号角色认证（通过账号分配管理员/普通用户权限）
- 📄 代理订阅配置文件上传、在线编辑、下载
- 🔗 一键复制订阅链接，导入代理客户端
- 📦 代理客户端中转下载（V2Ray、Clash Verge、V2RayNG、Clash Meta）
- ⏱️ 客户端文件自动缓存，1小时过期清理

## 快速开始

### 一键启动 / 停止

```bash
# 一键启动（自动检查并准备虚拟环境、依赖，后台启动前后端服务）
./start.sh

# 一键停止（安全终止前后端服务并释放端口）
./stop.sh
```

### 手动启动


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

- 统一登录入口：`https://node.undefinedip.com/` (或根据实际部署域名访问根目录)
- 管理员账号/密码: `admin` / `admin`
- 普通用户账号/密码: `user` / `user`

## 项目结构

详见 [index.md](./index.md)
