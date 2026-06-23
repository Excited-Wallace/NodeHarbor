# NodeHarbor 项目目录结构索引

> 代理节点管理平台 - FastAPI + Vue 3 全栈项目
> 技术栈: FastAPI / SQLite / Vue 3 / Element Plus / CodeMirror 6

```
NodeHarbor-1/
│
├── index.md                              # 📋 项目目录结构索引（本文件）
├── README.md                             # 📖 项目说明文档（部署指南、使用说明）
├── .gitignore                            # 🚫 Git 忽略规则
│
├── backend/                              # ===== 🐍 FastAPI 后端 =====
│   │
│   ├── app/                              # 应用主目录
│   │   ├── __init__.py                   # 包初始化
│   │   ├── main.py                       # FastAPI 应用入口
│   │   │                                 #   - 创建 FastAPI 实例
│   │   │                                 #   - 挂载路由、CORS 中间件
│   │   │                                 #   - 启动事件（初始化数据库、创建默认账号）
│   │   │
│   │   ├── config.py                     # 全局配置
│   │   │                                 #   - 数据库路径、JWT 密钥、Token 过期时间
│   │   │                                 #   - 上传目录路径、下载缓存目录路径
│   │   │                                 #   - 客户端缓存过期时间（1小时）
│   │   │
│   │   ├── database.py                   # 数据库连接与初始化
│   │   │                                 #   - SQLAlchemy engine 和 session 创建
│   │   │                                 #   - 建表逻辑、初始数据填充（默认账号）
│   │   │
│   │   ├── models.py                     # SQLAlchemy ORM 模型
│   │   │                                 #   - User: 用户表（role, password_hash）
│   │   │                                 #   - Config: 配置文件表（name, filename, description, file_size）
│   │   │                                 #   - ClientDownload: 客户端缓存记录表（client_name, platform, version, cached_at）
│   │   │
│   │   ├── schemas.py                    # Pydantic 请求/响应数据模型
│   │   │                                 #   - LoginRequest: 登录请求（password, role）
│   │   │                                 #   - TokenResponse: Token 响应
│   │   │                                 #   - ConfigResponse: 配置文件信息响应
│   │   │                                 #   - ClientInfo: 客户端信息响应
│   │   │
│   │   ├── auth.py                       # JWT 认证核心逻辑
│   │   │                                 #   - create_access_token(): 生成 JWT Token
│   │   │                                 #   - verify_token(): 验证并解析 Token
│   │   │                                 #   - hash_password() / verify_password(): 密码加密与校验
│   │   │
│   │   ├── dependencies.py               # FastAPI 依赖注入
│   │   │                                 #   - get_current_user(): 从请求头提取并验证用户
│   │   │                                 #   - require_admin(): 要求管理员权限的依赖
│   │   │                                 #   - get_db(): 获取数据库 session
│   │   │
│   │   ├── routers/                      # API 路由模块（按功能拆分）
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── auth.py                   # 认证路由
│   │   │   │                             #   POST /api/auth/login    - 密码登录（请求体: password + role）
│   │   │   │                             #   GET  /api/auth/me       - 获取当前登录用户信息
│   │   │   │
│   │   │   ├── configs.py                # 配置文件路由
│   │   │   │                             #   GET    /api/configs              - 获取配置文件列表
│   │   │   │                             #   POST   /api/configs/upload       - 上传 .yaml 配置文件 [管理员]
│   │   │   │                             #   GET    /api/configs/{id}         - 获取配置文件详情
│   │   │   │                             #   GET    /api/configs/{id}/download - 下载配置文件
│   │   │   │                             #   GET    /api/configs/{id}/content  - 获取文件文本内容 [管理员]
│   │   │   │                             #   PUT    /api/configs/{id}/content  - 更新文件内容 [管理员]
│   │   │   │                             #   DELETE /api/configs/{id}          - 删除配置文件 [管理员]
│   │   │   │
│   │   │   ├── clients.py                # 代理客户端下载路由
│   │   │   │                             #   GET  /api/clients                - 获取支持的客户端列表及版本
│   │   │   │                             #   POST /api/clients/{name}/fetch   - 触发服务器下载客户端到本地
│   │   │   │                             #   GET  /api/clients/{name}/download - 下载已缓存的客户端文件
│   │   │   │                             #   GET  /api/clients/{name}/status   - 查询下载进度
│   │   │   │
│   │   │   └── system.py                 # 系统信息路由
│   │   │                                 #   GET /api/system/status - 系统状态（磁盘、缓存等）[管理员]
│   │   │
│   │   ├── services/                     # 业务逻辑层（路由调用此层处理核心逻辑）
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── auth_service.py           # 认证业务逻辑
│   │   │   │                             #   - authenticate(): 验证密码并返回用户
│   │   │   │                             #   - init_default_users(): 初始化默认管理员和用户账号
│   │   │   │
│   │   │   ├── config_service.py         # 配置文件管理业务逻辑
│   │   │   │                             #   - save_config(): 保存上传的配置文件
│   │   │   │                             #   - get_config_content(): 读取配置文件文本
│   │   │   │                             #   - update_config_content(): 更新配置文件
│   │   │   │                             #   - delete_config(): 删除配置文件（数据库记录+磁盘文件）
│   │   │   │
│   │   │   └── client_service.py         # 客户端下载与缓存业务逻辑
│   │   │                                 #   - fetch_client(): 从 GitHub Release 下载客户端到本地
│   │   │                                 #   - get_cached_file(): 获取缓存文件（检查是否过期）
│   │   │                                 #   - cleanup_expired(): 清理过期缓存（>1小时）
│   │   │                                 #   - get_latest_release(): 查询 GitHub Release API 获取最新版本
│   │   │                                 #
│   │   │                                 #   支持的客户端及 GitHub 仓库：
│   │   │                                 #     V2Ray         - v2fly/v2ray-core (Windows/Linux/macOS)
│   │   │                                 #     Clash Verge   - clash-verge-rev/clash-verge-rev (Windows/Linux/macOS)
│   │   │                                 #     V2RayNG       - 2dust/v2rayNG (Android)
│   │   │                                 #     Clash Meta    - MetaCubeX/ClashMetaForAndroid (Android)
│   │   │
│   │   └── utils/                        # 工具函数
│   │       ├── __init__.py
│   │       │
│   │       ├── file_handler.py           # 文件操作工具
│   │       │                             #   - save_upload_file(): 保存上传文件到 uploads/ 目录
│   │       │                             #   - read_file_content(): 读取文件文本内容
│   │       │                             #   - delete_file(): 删除文件
│   │       │                             #   - get_file_size(): 获取文件大小
│   │       │
│   │       └── proxy_helper.py           # GitHub Release 辅助工具
│   │                                     #   - parse_release_assets(): 解析 GitHub Release 资源列表
│   │                                     #   - download_file(): 异步下载文件到本地
│   │                                     #   - get_release_info(): 调用 GitHub API 获取 Release 信息
│   │
│   ├── uploads/                          # 📁 上传的 .yaml 配置文件存储目录
│   │   └── .gitkeep
│   │
│   ├── downloads/                        # 📁 代理客户端缓存目录
│   │   └── .gitkeep                      #     文件在缓存 1 小时后自动过期删除
│   │
│   ├── data/                             # 📁 数据库文件目录
│   │   └── .gitkeep                      #     SQLite 数据库 nodeharbor.db 存放于此
│   │
│   ├── requirements.txt                  # 📦 Python 依赖清单
│   │                                     #   fastapi, uvicorn, sqlalchemy,
│   │                                     #   python-jose[cryptography], passlib[bcrypt],
│   │                                     #   python-multipart, aiohttp, pyyaml, aiofiles
│   │
│   └── .env                              # 🔐 环境变量（不提交 Git）
│                                         #   JWT_SECRET_KEY, DATABASE_URL 等
│
├── frontend/                             # ===== 🎨 Vue 3 前端 =====
│   │
│   ├── index.html                        # HTML 入口文件
│   ├── vite.config.js                    # Vite 构建配置（API 代理到后端等）
│   ├── package.json                      # 前端依赖和脚本配置
│   │
│   ├── public/                           # 静态资源（不经过 Vite 处理）
│   │   └── favicon.ico
│   │
│   └── src/                              # 前端源码
│       │
│       ├── main.js                       # Vue 应用入口
│       │                                 #   - 创建 Vue 实例
│       │                                 #   - 注册 Element Plus、Pinia、Router
│       │
│       ├── App.vue                       # 根组件
│       │
│       ├── router/                       # 路由配置
│       │   └── index.js                  # Vue Router 路由定义
│       │                                 #   默认路径 (/) 为用户界面，/admin 为管理员界面
│       │                                 #
│       │                                 #   用户路由：
│       │                                 #     /login           - 用户登录页
│       │                                 #     /                - 用户仪表盘
│       │                                 #     /configs         - 查看与下载配置
│       │                                 #     /clients         - 客户端下载
│       │                                 #
│       │                                 #   管理员路由：
│       │                                 #     /admin/login     - 管理员登录页
│       │                                 #     /admin           - 管理员仪表盘
│       │                                 #     /admin/configs   - 配置管理（CRUD）
│       │                                 #     /admin/configs/:id/edit - 在线编辑配置
│       │                                 #     /admin/clients   - 客户端下载
│       │
│       ├── stores/                       # Pinia 状态管理
│       │   ├── auth.js                   # 认证状态
│       │   │                             #   - token: JWT Token
│       │   │                             #   - role: 当前角色 (admin/user)
│       │   │                             #   - login() / logout() 方法
│       │   │
│       │   └── config.js                 # 配置文件状态
│       │                                 #   - configList: 配置文件列表
│       │                                 #   - fetchConfigs() / deleteConfig() 方法
│       │
│       ├── api/                          # API 请求封装（Axios）
│       │   ├── index.js                  # Axios 实例配置
│       │   │                             #   - baseURL 设置
│       │   │                             #   - 请求拦截器：自动附加 JWT Token
│       │   │                             #   - 响应拦截器：处理 401 跳转登录
│       │   │
│       │   ├── auth.js                   # 认证 API
│       │   │                             #   - login(password, role)
│       │   │                             #   - getMe()
│       │   │
│       │   ├── configs.js                # 配置文件 API
│       │   │                             #   - getConfigs() / uploadConfig() / downloadConfig()
│       │   │                             #   - getContent() / updateContent() / deleteConfig()
│       │   │
│       │   └── clients.js                # 客户端下载 API
│       │                                 #   - getClients() / fetchClient() / downloadClient()
│       │
│       ├── views/                        # 页面级组件
│       │   │
│       │   ├── LoginView.vue             # 登录页（用户和管理员共用）
│       │   │                             #   - 仅密码输入框，通过当前路由路径判断角色
│       │   │                             #   - 深色主题，品牌 Logo
│       │   │
│       │   ├── admin/                    # 管理员专属页面
│       │   │   ├── AdminDashboard.vue    # 管理员仪表盘
│       │   │   │                         #   - 配置文件数量统计
│       │   │   │                         #   - 系统状态概览
│       │   │   │                         #   - 快捷操作入口（上传/管理）
│       │   │   │
│       │   │   ├── ConfigManager.vue     # 配置文件管理
│       │   │   │                         #   - 表格展示所有配置文件
│       │   │   │                         #   - 上传新配置（拖拽上传）
│       │   │   │                         #   - 编辑/删除操作
│       │   │   │
│       │   │   └── ConfigEditor.vue      # 配置文件在线编辑
│       │   │                             #   - 集成 CodeMirror 6 编辑器
│       │   │                             #   - YAML 语法高亮
│       │   │                             #   - 保存/撤销功能
│       │   │
│       │   ├── user/                     # 用户专属页面
│       │   │   ├── UserDashboard.vue     # 用户仪表盘
│       │   │   │                         #   - 可用配置数量
│       │   │   │                         #   - 快速下载入口
│       │   │   │
│       │   │   └── ConfigList.vue        # 配置文件查看与下载
│       │   │                             #   - 卡片展示配置文件列表
│       │   │                             #   - 下载 .yaml 文件
│       │   │                             #   - 复制订阅链接（供客户端导入）
│       │   │
│       │   ├── ClientsView.vue           # 代理客户端下载页（管理员/用户共用）
│       │   │                             #   - 按客户端分类展示
│       │   │                             #   - 全平台下载选项
│       │   │                             #   - 下载进度实时显示
│       │   │
│       │   └── NotFoundView.vue          # 404 页面
│       │
│       ├── components/                   # 可复用组件
│       │   │
│       │   ├── layout/                   # 布局组件
│       │   │   ├── AppHeader.vue         # 顶部导航栏（Logo、角色显示、退出按钮）
│       │   │   ├── AppSidebar.vue        # 侧边栏导航（根据角色显示不同菜单项）
│       │   │   └── AppLayout.vue         # 整体布局容器（Header + Sidebar + Content）
│       │   │
│       │   ├── config/                   # 配置相关组件
│       │   │   ├── ConfigCard.vue        # 配置文件卡片（名称、描述、大小、下载按钮）
│       │   │   └── YamlEditor.vue        # YAML 编辑器封装（CodeMirror 6 实例化与配置）
│       │   │
│       │   ├── client/                   # 客户端相关组件
│       │   │   └── ClientCard.vue        # 客户端下载卡片（客户端图标、平台选择、下载按钮）
│       │   │
│       │   └── common/                   # 通用组件
│       │       ├── LoadingSpinner.vue    # 加载动画（全屏/局部）
│       │       └── ConfirmDialog.vue     # 确认对话框（删除等危险操作前确认）
│       │
│       └── assets/                       # 静态资源
│           ├── styles/
│           │   ├── main.css              # 全局样式（重置样式、通用类）
│           │   └── variables.css         # CSS 变量（颜色、间距、圆角、阴影等设计 Token）
│           │
│           └── images/                   # 图标和图片资源
│               └── .gitkeep
```

## 数据库设计

### users 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| role | TEXT UNIQUE | 角色（admin / user） |
| password_hash | TEXT | bcrypt 加密密码，默认密码 `admin` |
| created_at | DATETIME | 创建时间 |

### configs 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| name | TEXT | 配置文件显示名称 |
| filename | TEXT | 实际存储文件名 |
| description | TEXT | 配置描述 |
| file_size | INTEGER | 文件大小（字节） |
| created_at | DATETIME | 上传时间 |
| updated_at | DATETIME | 最后修改时间 |

### client_downloads 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| client_name | TEXT | 客户端名称 |
| platform | TEXT | 平台（windows/linux/macos/android） |
| version | TEXT | 版本号 |
| filename | TEXT | 缓存文件名 |
| file_size | INTEGER | 文件大小 |
| download_url | TEXT | GitHub 原始下载地址 |
| cached_at | DATETIME | 缓存时间（1小时过期） |
