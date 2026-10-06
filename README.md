# IMCJK 个人博客与全栈网站系统 (Python FastAPI 生产重构版)

基于 **Python 3.12 + FastAPI + SQLAlchemy 2.0 Async + MySQL 8.0 + Redis 7.2** 构建的高性能全异步个人全栈博客系统，完整包含 4 个 Vue 3 SPA 独立端、React Native / Expo 移动端管理 App，以及城市足迹、矢量地图与城市图集走廊。

本项目已完成从原 Java / Spring Boot 3 架构的完整生产级重构，当前作为唯一主线长期稳定运行于阿里云 2C2G 生产环境中，物理内存占用较老版本净释放 240MB+，零 OOM 风险。

---

## 🏛️ 整体架构一览

```text
                               公网用户访问
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    ▼                               ▼                               ▼
blog.imcjk.top                  admin.imcjk.top                 imcjk.top / cv.imcjk.top
(Vue 3 博客前台)               (Vue 3 管理后台)               (门户主站 / 个人简历)
    │                               │                               │
    └───────────────────────┬───────┴───────────────────────────────┘
                            ▼
                Nginx 1.28.0 反向代理网关 (80 / 443 SSL)
                  ├── 静态直出: HTML / JS / 6.6MB city.json GeoJSON
                  ├── 防盗链防护: Referrer-Policy "no-referrer"
                  └── 协议升级: WebSocket /api/ws/online
                            │
                            ▼
                FastAPI 异步内核 (Uvicorn 127.0.0.1:8082, 1 Worker)
                  ├── 统一信封: {code: 1, msg: null, data: ...}
                  ├── 驼峰直出: CamelModel + yyyy-MM-dd HH:mm
                  ├── 宽容绑定: LenientQueryModel (空值回落默认)
                  └── 自动事务: deps.get_db_session (commit/rollback)
                            │
         ┌──────────────────┴──────────────────┐
         ▼                                     ▼
MySQL 8.0 (feitwnd 库 / 21 张物理表)   Redis 7.2 (DB 1 隔离库 / imcjk: 前缀)
         │                                     │
         ▼                                     ▼
阿里云 OSS (流式直传 WebP 图片与音频)    QQ SMTP (SSL 465 验证码与邮件通知)
```

---

## 🌟 核心功能与特性

### 1. 博客前台 (Frontend-Blog)
* **文章瀑布流与全文搜索**：支持 Markdown / HTML 双重净化渲染、代码块高亮、目录提取与阅读时间预估；
* **城市足迹与图集 (最新上游同步)**：ECharts 中国地图矢量高亮游历省市，散点点击联动横向轮播图集走廊；
* **时间轴归档**：按年、月分组的时间轴足迹归档；
* **背景音乐播放器**：支持 OSS 音频直链播放、实时歌词同步；
* **在线访客统计**：基于原生 WebSocket 心跳实时广播当前全站在线人数。

### 2. 管理后台 (Frontend-Admin)
* **大屏仪表盘**：全站 PV 趋势折线图、访客省份分布饼图、Top 10 热门文章排行；
* **足迹与图集管理**：省市级联选择器录入、游历时间拾取、多图 OSS 直传、拖拽权重排序与批量级联删除；
* **内容管理**：文章 CRUD（支持置顶、发布状态筛选、草稿保存）、分类与标签树状字典；
* **互动审核**：评论与留言两级树状盖楼审核、回复、表情包选择器；
* **安全审计**：管理员操作日志跟踪、访客指纹档案与真实公网 IP 记录。

### 3. 移动端 App (App)
* 基于 **React Native / Expo** 编写，与管理端共用底层 API；
* 支持 Expo Go 极速扫码预览或 EAS 一键云端构建 Android APK。

---

## 📁 模块结构

```text
├── Backend/                 # Python 3.12 / FastAPI 完整异步后端工程
│   ├── app/                 # 核心代码 (core, db, integrations, modules, ws)
│   ├── requirements.txt     # 纯净生产依赖
│   ├── Dockerfile           # 后端容器构建镜像
│   └── README.md            # 后端深度技术设计文档
├── Frontend-Blog/           # 博客前台 SPA (Vue 3 + Vite + ECharts + Element Plus)
├── Frontend-Admin/          # 管理后台 SPA (Vue 3 + Vite + Pinia + Element Plus)
├── Frontend-Home/           # 门户主站 SPA
├── Frontend-Cv/             # 个人在线简历 SPA
├── App/                     # 移动端管理 App (React Native / Expo)
├── docker-compose.yml       # 全栈本地一键编排启动配置
├── TECHNICAL_ARCHITECTURE.md# 系统全景技术架构设计与决策记录
└── ALIYUN_MIGRATION_REPORT.md # 生产环境迁移与稳定性报告
```

---

## 🚀 本地快速启动

### 方式一：Docker Compose 一键启动

```bash
cp Backend/.env.example Backend/.env
# 配置 Backend/.env 中的数据库与 Redis 凭证
docker-compose up -d --build
```

### 方式二：本地开发模式

```bash
# 1. 启动后端
cd Backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload

# 2. 启动博客前台
cd ../Frontend-Blog
pnpm install
pnpm dev

# 3. 启动管理后台
cd ../Frontend-Admin
pnpm install
pnpm dev
```

---

## 📜 开源协议

本项目采用 [MIT License](LICENSE) 授权许可。
