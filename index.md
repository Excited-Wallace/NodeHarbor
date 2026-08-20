# NodeHarbor 项目目录结构与架构索引

> **NodeHarbor** - 现代化代理订阅管理与多平台客户端聚合中转分发平台  
> **技术栈**: FastAPI (Python 3.10+) / SQLite + SQLAlchemy 2.0 / Vue 3 / Vite / Element Plus / CodeMirror 6

```
NodeHarbor/
│
├── index.md                              # 📋 项目目录结构与架构索引（本文件）
├── README.md                             # 📖 项目说明文档（技术栈、功能特性、快速上手指南）
├── LICENSE                               # 📜 GPL-3.0 开源许可证
├── .gitignore                            # 🚫 Git 忽略规则文件
├── start.sh                              # 🚀 一键启动脚本（虚拟环境检测、依赖安装、前后端后台启动与健康检查）
├── stop.sh                               # 🛑 一键停止脚本（优雅终止、超时强杀、端口清理）
│
├── logs/                                 # 📑 运行时日志与进程 PID 目录
│   ├── backend.log                       # FastAPI 后端运行标准输出与错误日志
│   ├── frontend.log                      # Vite 前端开发服务器输出日志
│   ├── backend.pid                       # 后端进程 PID 记录文件
│   └── frontend.pid                      # 前端进程 PID 记录文件
│
├── backend/                              # ==================== 🐍 FastAPI 后端 ====================
│   │
│   ├── app/                              # 后端应用核心源码目录
│   │   ├── __init__.py                   # 包初始化标识文件
│   │   ├── main.py                       # FastAPI 应用入口与生命周期管理
│   │   │                                 #   - 创建 FastAPI 实例并配置全局 CORS 中间件
│   │   │                                 #   - lifespan 生命周期管理：自动建表、数据库平滑迁移 (migrate_database)
│   │   │                                 #   - 启动双后台异步轮询定时器：
│   │   │                                 #       1. 客户端二进制安装包缓存清理 (background_cleanup_scheduler, 60s)
│   │   │                                 #       2. 订阅配置定时自动拉取更新 (background_config_update_scheduler, 30s)
│   │   │                                 #   - 挂载业务路由：/api/auth, /api/configs, /api/clients, /api/system
│   │   │
│   │   ├── config.py                     # 全局环境变量与路径配置
│   │   │                                 #   - 数据库连接 URL (SQLite nodeharbor.db)
│   │   │                                 #   - JWT 密钥与 Token 7 天有效期配置
│   │   │                                 #   - 文件存储路径：DATA_DIR (data/), UPLOAD_DIR (uploads/), DOWNLOAD_DIR (downloads/)
│   │   │
│   │   ├── database.py                   # 数据库引擎与会话管理
│   │   │                                 #   - SQLAlchemy 2.0 Engine 与 SessionLocal 工厂
│   │   │                                 #   - get_db() FastAPI 依赖注入生成器
│   │   │                                 #   - migrate_database() 自动检测并平滑补充新增数据表字段
│   │   │
│   │   ├── models.py                     # SQLAlchemy ORM 数据模型
│   │   │                                 #   - User: 用户账号表（username, password_hash, role: admin/user）
│   │   │                                 #   - Config: 订阅配置表（name, filename, is_public, subscription_url, auto_update, update_interval_type, update_time 等）
│   │   │                                 #   - ClientDownload: 客户端安装包缓存表（client_name, asset_id, platform, version, filename, file_size, cached_at）
│   │   │                                 #   - ClientReleaseCache: GitHub Release 24 小时元数据缓存表（tag_name, assets_json, fetched_at 等）
│   │   │
│   │   ├── schemas.py                    # Pydantic 请求与响应数据结构定义
│   │   │                                 #   - 认证模型: LoginRequest, TokenResponse, UserInfo
│   │   │                                 #   - 配置模型: ConfigResponse, ConfigCreate, ConfigVisibilityUpdate, ConfigScheduleUpdate, ConfigContentUpdate
│   │   │                                 #   - 客户端模型: ClientCardInfo, ClientReleaseAsset, ClientReleaseInfo, DownloadCacheRequest, DownloadTaskStatus, CacheStorageStatus
│   │   │                                 #   - 系统监控模型: SystemStatusResponse
│   │   │
│   │   ├── auth.py                       # JWT 认证与密码加密核心算法
│   │   │                                 #   - create_access_token(): 签发附带 sub 与 role 载荷的 JWT Token
│   │   │                                 #   - verify_token(): 解析并验证 Token 有效性
│   │   │                                 #   - hash_password() / verify_password(): 基于 bcrypt 的密码单向散列与校验
│   │   │
│   │   ├── dependencies.py               # FastAPI 权限与依赖注入中间件
│   │   │                                 #   - get_current_user(): 从 Authorization 头提取 Bearer Token 并校验当前登录用户
│   │   │                                 #   - require_admin(): 鉴权并强制要求管理员 (admin) 权限
│   │   │                                 #   - get_db(): 数据库 Session 请求级生命周期注入
│   │   │
│   │   ├── routers/                      # API 路由控制层（按功能模块划分）
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── auth.py                   # 🔐 认证路由
│   │   │   │                             #   POST /api/auth/login    - 账号密码登录（返回 access_token 与 role）
│   │   │   │                             #   GET  /api/auth/me       - 获取当前登录用户信息
│   │   │   │
│   │   │   ├── users.py                  # 👥 用户管理路由 [管理员]
│   │   │   │                             #   GET    /api/users        - 获取系统中所有用户列表
│   │   │   │                             #   POST   /api/users        - 管理员新增用户账号
│   │   │   │                             #   PUT    /api/users/{id}   - 管理员修改用户密码与角色
│   │   │   │                             #   DELETE /api/users/{id}   - 管理员删除用户 (含防删自身/唯一管理员校验)
│   │   │   │
│   │   │   ├── configs.py                # 📄 代理订阅配置路由
│   │   │   │                             #   GET    /api/configs               - 获取配置列表（普通用户仅可见 is_public=True）
│   │   │   │                             #   POST   /api/configs/upload        - 新增配置 [管理员] (支持本地文件/URL订阅/文本粘贴三种模式)
│   │   │   │                             #   PATCH  /api/configs/{id}/visibility - 切换普通用户可见性状态 [管理员]
│   │   │   │                             #   PUT    /api/configs/{id}/schedule - 修改定时自动更新策略与时间 [管理员]
│   │   │   │                             #   POST   /api/configs/{id}/sync     - 立即手动触发从订阅源拉取更新 [管理员]
│   │   │   │                             #   GET    /api/configs/{id}          - 获取指定配置详情
│   │   │   │                             #   GET    /api/configs/{id}/download - 免登录公开订阅直链（供客户端直接拉取 YAML 配置）
│   │   │   │                             #   GET    /api/configs/{id}/content  - 读取配置 YAML 文本内容（供在线预览或编辑）
│   │   │   │                             #   PUT    /api/configs/{id}/content  - 保存修改后的 YAML 文本内容 [管理员]
│   │   │   │                             #   DELETE /api/configs/{id}          - 删除配置（同步清理数据库记录与磁盘文件）[管理员]
│   │   │   │
│   │   │   ├── clients.py                # 📦 代理客户端与 GitHub Release 路由
│   │   │   │                             #   GET  /api/clients                           - 获取 4 个支持的客户端基础卡片信息
│   │   │   │                             #   GET  /api/clients/{client_id}/release       - 获取最新 Release 及 Assets 列表（24h 缓存，支持 force_refresh）
│   │   │   │                             #   POST /api/clients/cache                     - 触发服务端异步中转下载安装包到本地缓存
│   │   │   │                             #   GET  /api/clients/tasks/{task_id}           - 轮询查询服务端异步下载任务实时进度
│   │   │   │                             #   GET  /api/clients/download/{client_id}/{fn} - 从服务器直接高速下载已缓存的安装包
│   │   │   │                             #   GET  /api/clients/cache-status              - 获取服务端缓存容量状态（已用 MB / 512MB 上限）
│   │   │   │                             #   POST /api/clients/cache/clear               - 管理员一键清空所有客户端安装包缓存与临时文件 [管理员]
│   │   │   │
│   │   │   └── system.py                 # 📊 系统状态与监控路由
│   │   │                                 #   GET  /api/system/status - 查询系统状态（数据库大小、用户总数、配置总数、缓存大小等）[管理员]
│   │   │
│   │   ├── services/                     # 业务服务层（核心业务逻辑封装）
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── auth_service.py           # 认证业务逻辑
│   │   │   │                             #   - authenticate(): 校验账号密码并返回用户模型
│   │   │   │                             #   - init_default_users(): 初始化系统默认 admin/user 账号
│   │   │   │
│   │   │   ├── user_service.py           # 用户管理业务逻辑
│   │   │   │                             #   - get_all_users(): 查询全量用户列表
│   │   │   │                             #   - create_user(): 唯一性检查、bcrypt 密码哈希与新增账号
│   │   │   │                             #   - update_user(): 密码重置、角色变更与唯一管理员防降级保护
│   │   │   │                             #   - delete_user(): 防删除当前登录账号与防删除唯一管理员校验
│   │   │   │
│   │   │   ├── config_service.py         # 代理配置管理与定时同步业务逻辑
│   │   │   │                             #   - save_config_from_file(): 保存上传的 .yaml 文件
│   │   │   │                             #   - save_config_from_url(): 从外部订阅 URL 拉取并保存，初始化定时配置
│   │   │   │                             #   - save_config_from_content(): 直接保存粘贴的 YAML 文本
│   │   │   │                             #   - sync_subscription_config(): 立即从外部源异步同步最新配置
│   │   │   │                             #   - update_config_visibility(): 切换配置公开/隐藏属性
│   │   │   │                             #   - update_config_schedule(): 调整定时自动更新模式与时间
│   │   │   │                             #   - background_config_update_scheduler(): 后台定时检查并自动拉取更新
│   │   │   │                             #   - get_config_content() / update_config_content() / delete_config()
│   │   │   │
│   │   │   └── client_service.py         # 客户端 Release 缓存与中转下载业务逻辑
│   │   │                                 #   - CLIENTS_CONFIG: 4 个客户端官方仓库配置 (v2rayN, v2rayNG, Clash Verge Rev, Clash Meta Android)
│   │   │                                 #   - get_client_release_info(): 24 小时 Release 元数据本地持久化缓存
│   │   │                                 #   - DownloadManager: 异步并发下载管理器，流式拉取、进度测速与任务状态维护
│   │   │                                 #   - get_cache_storage_status() / clear_all_cache(): 缓存容量监控与一键清理
│   │   │                                 #   - background_cleanup_scheduler(): 60 秒轮询清理超过 1 小时的安装包与超限淘汰
│   │   │
│   │   └── utils/                        # 辅助工具模块
│   │       ├── __init__.py
│   │       ├── file_handler.py           # 磁盘文件 I/O 工具（安全写入、读取、删除、计算体积）
│   │       └── proxy_helper.py           # GitHub API 请求与 Assets 资源解析辅助工具
│   │
│   ├── uploads/                          # 📁 用户上传与拉取的代理 .yaml 配置文件物理存储目录
│   │   └── .gitkeep
│   │
│   ├── downloads/                        # 📁 服务端中转缓存的客户端安装包目录（1 小时有效期，最大 512MB）
│   │   └── .gitkeep
│   │
│   ├── data/                             # 📁 SQLite 数据库持久化目录（存储 nodeharbor.db）
│   │   └── .gitkeep
│   │
│   ├── requirements.txt                  # 📦 Python 后端依赖清单 (fastapi, uvicorn, sqlalchemy, aiohttp, pyyaml, etc.)
│   └── .env                              # 🔐 运行时环境变量（可选覆盖端口、密钥等）
│
└── frontend/                             # ==================== 🎨 Vue 3 前端 ====================
    │
    ├── index.html                        # HTML 模板入口
    ├── vite.config.js                    # Vite 工程构建与开发服务器配置（反向代理 /api 至后端）
    ├── package.json                      # 前端 Node.js 依赖与运行脚本清单
    │
    ├── public/                           # 前端公共静态资源
    │   ├── favicon.svg                   # 网站现代化 SVG 矢量图标
    │   └── icons.svg                     # 常用客户端与平台 SVG 图标合集
    │
    └── src/                              # 前端源码目录
        │
        ├── main.js                       # Vue 应用程序主入口（注册 Pinia、Router、Element Plus）
        ├── App.vue                       # 应用根组件（全局暗色容器与基础样式挂载）
        │
        ├── router/                       # 路由系统
        │   └── index.js                  # Vue Router 路由定义与基于角色权限的全局导航守卫
        │                                 #   统一登录：/login
        │                                 #   用户路由：/ (用户仪表盘), /configs (用户配置), /clients (客户端下载)
        │                                 #   管理员路由：/admin (管理员仪表盘), /admin/configs (配置管理),
        │                                 #             /admin/configs/:id/edit (在线编辑), /admin/users (用户管理),
        │                                 #             /admin/clients (客户端下载)
        │
        ├── stores/                       # Pinia 响应式状态管理
        │   ├── auth.js                   # 用户认证状态 (Token、用户名、Role、登录/退出逻辑)
        │   ├── config.js                 # 订阅配置状态流 (配置列表获取、增删改、刷新)
        │   └── device.js                 # 设备响应式视口状态 (检测是否为移动端设备，适配布局)
        │
        ├── api/                          # Axios API 请求统一封装
        │   ├── index.js                  # Axios 实例配置、全局请求头注入 JWT Bearer Token、401 拦截处理
        │   ├── auth.js                   # 登录与获取当前用户 API
        │   ├── users.js                  # 用户列表查询、新增用户、密码修改与删除 API
        │   ├── configs.js                # 配置列表、上传导入、可见性修改、定时设置、手动同步、编辑与删除 API
        │   └── clients.js                # 客户端卡片、Release 详情、服务端缓存触发、进度查询、缓存状态与一键清理 API
        │
        ├── views/                        # 页面级视图组件
        │   │
        │   ├── Login.vue                 # 统一登录页（深色拟态、角色自适应跳转）
        │   │
        │   ├── admin/                    # 🛠️ 管理员专属视图
        │   │   ├── AdminDashboard.vue    # 管理员仪表盘（系统用户与配置统计、客户端缓存监控、快捷操作卡片）
        │   │   ├── UserManager.vue       # 用户管理大厅（用户列表、密码重置、角色分配、新增与删除安全防护）
        │   │   ├── ConfigManager.vue     # 配置管理大厅（表格列表、导入弹窗、可见性切换、定时策略设置、手动同步）
        │   │   └── ConfigEditor.vue      # 配置文件在线编辑页（集成 CodeMirror 6，YAML 语法高亮与保存）
        │   │
        │   ├── user/                     # 👤 普通用户专属视图
        │   │   ├── UserDashboard.vue     # 普通用户仪表盘（可用配置概览、一键快捷复制与跳转）
        │   │   └── ConfigList.vue        # 代理配置下载大厅（卡片展示、一键复制免登录订阅直链、文件下载、在线预览）
        │   │
        │   ├── ClientsView.vue           # 📦 代理客户端下载大厅（管理员/普通用户通用，卡片展示与版本选择弹窗）
        │   └── NotFoundView.vue          # 404 缺省错误页
        │
        ├── components/                   # 可复用业务与通用组件
        │   │
        │   ├── layout/                   # 布局组件
        │   │   ├── AppHeader.vue         # 顶部导航栏（Logo、用户角色标识、退出登录）
        │   │   ├── AppSidebar.vue        # 桌面端侧边导航栏（根据管理员/普通用户角色动态渲染菜单）
        │   │   ├── AppLayout.vue         # 页面主布局框架容器（Header + Sidebar + View Content + MobileBottomNav）
        │   │   └── MobileBottomNav.vue   # 移动端专属底部沉浸式快捷导航栏
        │   │
        │   ├── config/                   # 配置相关业务组件
        │   │   ├── ConfigCard.vue        # 配置卡片组件（名称、描述、体积、复制订阅直链、下载按钮）
        │   │   └── YamlEditor.vue        # 基于 CodeMirror 6 封装的 YAML 高亮编辑器组件
        │   │
        │   ├── client/                   # 客户端相关业务组件
        │   │   ├── ClientCard.vue        # 客户端信息卡片（图标、平台标签、GitHub 仓库链接、版本选择触发按钮）
        │   │   └── ClientReleaseModal.vue # 客户端最新 Release 详情与 Assets 选择弹窗（服务端中转下载与实时进度条）
        │   │
        │   └── common/                   # 通用基础组件
        │       ├── LoadingSpinner.vue    # 加载状态指示器
        │       └── ConfirmDialog.vue     # 操作二次确认对话框（删除配置、清空缓存前确认）
        │
        └── assets/                       # 静态媒体与全局样式资产
            ├── hero.png                  # 仪表盘与登录背景氛围图
            └── styles/
                ├── main.css              # 全局 CSS 重置、暗黑主题变量与通用原子类
                └── variables.css         # CSS 自定义属性设计 Token（调色板、圆角、毛玻璃与阴影）
```

---

## 🗄️ 数据库设计规范

SQLite 数据库文件持久化于 `backend/data/nodeharbor.db`，由 SQLAlchemy ORM 管理。包含以下 4 张核心数据表：

### 1. `users` 用户账号表
| 字段名 | 类型 | 约束 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | - | 用户主键 ID |
| `username` | VARCHAR | UNIQUE, INDEX, NOT NULL | - | 登录账号名（如 `admin`, `user`） |
| `role` | VARCHAR | INDEX, NOT NULL | - | 角色权限（`admin` 管理员 / `user` 普通用户） |
| `password_hash` | VARCHAR | NOT NULL | - | 基于 bcrypt 算法单向哈希加密的密码文本 |
| `created_at` | DATETIME | NOT NULL | `utcnow` | 账号注册/创建时间戳 |

### 2. `configs` 代理订阅配置表
| 字段名 | 类型 | 约束 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | - | 配置主键 ID |
| `name` | VARCHAR | INDEX, NOT NULL | - | 配置文件自定义显示名称 |
| `filename` | VARCHAR | NOT NULL | - | 存储于 `backend/uploads/` 的物理文件名 |
| `description` | VARCHAR | NULLABLE | `NULL` | 配置文件的详细说明与备注 |
| `file_size` | INTEGER | NOT NULL | `0` | 配置文件大小（字节） |
| `is_public` | BOOLEAN | NOT NULL | `True` | 是否对普通用户可见（`True` 可见 / `False` 隐藏） |
| `subscription_url` | VARCHAR | NULLABLE | `NULL` | 外部订阅源原始 URL 地址 |
| `auto_update` | BOOLEAN | NOT NULL | `False` | 是否开启后台定时自动拉取更新 |
| `update_interval_type`| VARCHAR | NULLABLE | `'daily'` | 定时模式（`daily` 每日指定时间 / `interval` 固定间隔小时）|
| `update_time` | VARCHAR | NULLABLE | `'04:00'` | 设定的定时时间值（如 `'04:00'` 或 `'12'`） |
| `last_auto_update_at` | DATETIME | NULLABLE | `NULL` | 上一次自动同步更新成功的 UTC 时间戳 |
| `last_auto_update_status`| VARCHAR| NULLABLE | `NULL` | 上一次自动同步执行状态（`success` 或具体错误详情） |
| `created_at` | DATETIME | NOT NULL | `utcnow` | 配置创建/首次上传时间 |
| `updated_at` | DATETIME | NOT NULL | `utcnow` | 配置内容最后一次变更时间 |

### 3. `client_downloads` 客户端安装包缓存表
| 字段名 | 类型 | 约束 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | - | 缓存记录主键 ID |
| `client_name` | VARCHAR | INDEX, NOT NULL | - | 客户端标识（`v2rayn`, `v2rayng`, `clash-verge`, `clash-meta-android`） |
| `asset_id` | VARCHAR | INDEX, NULLABLE | `NULL` | 对应的 GitHub Release Asset ID |
| `platform` | VARCHAR | NULLABLE | `NULL` | 适用操作系统平台（`windows`, `android`, `macos`, `linux`） |
| `version` | VARCHAR | NOT NULL | - | 客户端版本号（例如 `7.24.4`） |
| `filename` | VARCHAR | NOT NULL | - | 缓存在 `backend/downloads/` 的物理文件名 |
| `file_size` | INTEGER | NOT NULL | `0` | 缓存文件大小（字节） |
| `download_url` | VARCHAR | NOT NULL | - | GitHub 官方原始下载直链 |
| `cached_at` | DATETIME | NOT NULL | `utcnow` | 缓存下载完成时间（用于 1 小时过期判断） |

### 4. `client_release_cache` GitHub Release 元数据缓存表
| 字段名 | 类型 | 约束 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | - | 缓存主键 ID |
| `client_name` | VARCHAR | UNIQUE, INDEX, NOT NULL | - | 客户端标识（唯一索引） |
| `tag_name` | VARCHAR | NOT NULL | - | 最新 Release 版本 Tag（如 `v2.5.2`） |
| `release_name` | VARCHAR | NULLABLE | `NULL` | GitHub Release 标题文本 |
| `published_at` | VARCHAR | NULLABLE | `NULL` | GitHub Release 官方发布时间字符串 |
| `html_url` | VARCHAR | NOT NULL | - | GitHub Release 详情页面 Web URL |
| `body` | TEXT | NULLABLE | `NULL` | Release 官方更新日志正文（Markdown 文本） |
| `assets_json` | TEXT | NOT NULL | - | JSON 序列化的全部资产列表（包含 asset ID, 文件名, 体积, 下载链接等） |
| `fetched_at` | DATETIME | NOT NULL | `utcnow` | 抓取时间（24 小时内直接复用本地缓存） |

---

## ⚙️ 核心交互与机制说明

1. **免登录代理订阅分发**
   - 端点：`GET /api/configs/{id}/download`
   - 为避免客户端每次更新订阅都需要 JWT 认证，系统将该端点设计为公开路由，响应头中携带 `Content-Disposition: inline` 与 `profile-update-interval: 24`，客户端（如 Clash / Shadowrocket）可直接添加为订阅地址。
2. **多级客户端缓存与中转加速**
   - **元数据缓存**：客户端首次访问时向 GitHub API 查询并将 Release 信息缓存至 `client_release_cache` 表，24 小时内不重复调用 GitHub API。
   - **服务端流式中转**：用户点击下载时，触发服务端后台下载任务，前端实时轮询 `/api/clients/tasks/{task_id}` 获取速度与进度条；
   - **有效期与淘汰策略**：下载完成的安装包物理文件缓存于 `downloads/` 目录，单文件保留 1 小时；后台调度器每 60 秒自动清理过期文件；总缓存设置 512MB 上限并支持管理员一键立即清空。
3. **订阅配置定时自动更新调度**
   - 管理员配置定时策略后，后台 `background_config_update_scheduler` 每 30 秒轮询数据库中 `auto_update=True` 的项，根据 `update_interval_type`（每日指定时刻或固定间隔小时）自动拉取外部订阅并覆盖更新磁盘配置，同时记录更新时间与状态。
4. **移动端沉浸式体验适配**
   - 通过 `stores/device.js` 实时响应窗口变化；在移动端隐藏侧边栏并启用 `MobileBottomNav.vue` 底部快捷导航，各页面卡片自动切换为移动端单列流式布局。
