# IMCJK 个人博客与全栈网站系统 (Python FastAPI 生产重构版)

基于 **Python 3.12 + FastAPI + SQLAlchemy 2.0 Async + MySQL 8.0 + Redis 7.2** 构建的高性能全异步个人全栈博客系统，完整包含 4 个 Vue 3 SPA 独立端、React Native / Expo 移动端管理 App，以及城市足迹、矢量地图与城市图集走廊。

本项目已完成从原 Java / Spring Boot 3 架构的完整生产级重构，当前作为唯一主线长期稳定运行于阿里云 2C2G 生产环境中，物理内存占用较老版本净释放 240MB+，零 OOM 风险。

---

## 🏛️ 系统总体技术架构拓扑

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

## 📁 全栈高精度源码目录树

```text
Kang-debug0426/blog/
├── Backend/                                    # 🐍 后端核心工程 (Python 3.12 / FastAPI / 异步单体)
│   ├── app/                                    # 源码主目录
│   │   ├── core/                               # 🌟 基础设施与通用内核
│   │   │   ├── config.py                       # Pydantic Settings 配置树 (从 .env 解析全站配置)
│   │   │   ├── deps.py                         # 依赖注入容器 (get_db_session 请求级自动 Commit/Rollback 事务闭环)
│   │   │   ├── errors.py                       # 业务异常模型与统一信封 Envelope 模型
│   │   │   ├── legacy_types.py                 # Java 历史格式兼容层 (CamelModel 驼峰序列化器、日期截秒规范)
│   │   │   ├── logging.py                      # 统一标准日志输出与格式化装配
│   │   │   ├── query.py                        # 宽容查询参数解析基类 (LenientQueryModel，空值转 None / 回落默认值)
│   │   │   ├── rate_limit.py                   # 基于 Redis 令牌桶算法的高频接口防刷切面
│   │   │   └── security.py                     # 密码学套件 (PBKDF2/SHA256 渐进升级、JWT 编解码校验)
│   │   │
│   │   ├── db/                                 # 🗄️ 数据库连接与 ORM 模型
│   │   │   ├── base.py                         # SQLAlchemy 2.0 声明基类与列定义宏 (PK, Int, TinyInt, LegacyDateTimeColumn)
│   │   │   ├── session.py                      # 异步数据库引擎 (create_async_engine) 与 AsyncSession 事务工厂
│   │   │   └── models/                         # 21 个物理表 ORM 映射模型 (按领域切片)
│   │   │       ├── admin.py                    # Admin 实体模型 (admin 表)
│   │   │       ├── article.py                  # 文章领域模型 (articles, article_categories, article_tags, article_tag_relations)
│   │   │       ├── engagement.py               # 互动领域模型 (article_comments, article_likes, messages, views, visitors)
│   │   │       ├── footprint.py                # 【最新】足迹与图集模型 (city_footprints, city_images)
│   │   │       ├── ops.py                      # 运维与日志模型 (operation_logs, rss_subscriptions)
│   │   │       └── site_content.py             # 站点内容模型 (personal_info, skills, experiences, social_media, music, friend_links, system_config)
│   │   │
│   │   ├── integrations/                       # 🔌 外部第三方基础设施适配器
│   │   │   ├── oss.py                          # 阿里云 OSS (基于 oss2 客户端的文件分类上传、WebP 流式直传)
│   │   │   ├── redis.py                        # 异步 Redis 连接池 (DB 1 隔离区、imcjk: 业务键命名空间封装)
│   │   │   └── smtp.py                         # QQ 邮箱 SMTP 安全传输 (SSL 465 异步发信、验证码通知)
│   │   │
│   │   ├── modules/                            # 💼 领域业务模块 (垂直拆分: Router -> Service -> Repository -> Schema)
│   │   │   ├── article/                        # 📝 文章创作域 (CRUD、分类标签、全文搜索、归档时间轴)
│   │   │   ├── auth/                           # 🔐 认证鉴权域 (动态验证码校验、Token 签发与作废)
│   │   │   ├── comments/                       # 💬 互动评论域 (两级树状盖楼组装、敏感词过滤、审核)
│   │   │   ├── footprint/                      # 🗺️ 【最新】城市足迹与图集域 (城市 CRUD、级联删除、公开地图接口)
│   │   │   ├── interaction/                    # 👍 轻互动域 (文章点赞防重与状态查询)
│   │   │   ├── misc/                           # 🛠️ 杂项与网关域 (/health、统一文件上传、Sitemap、RSS)
│   │   │   ├── ops/                            # 📊 运维审计域 (真实公网 IP 还原、访客指纹统计、RSS 订阅)
│   │   │   ├── report/                         # 📈 统计报表域 (PV/UV 趋势、省份分布、Top10 热文)
│   │   │   ├── site_content/                   # 🪪 站点内容域 (4 端个人信息投影、音乐播放列表、系统扩展配置)
│   │   │   └── taxonomy/                       # 🏷️ 分类与标签字典域
│   │   │
│   │   ├── ws/                                 # ⚡ 实时长连接域
│   │   │   └── router.py                       # /api/ws/online (WebSocket 心跳握手与在线访客计数)
│   │   │
│   │   └── main.py                             # 🏭 应用启动与装配入口 (中间件注入、路由挂载、异常拦截)
│   │
│   ├── Dockerfile                              # 后端轻量容器构建清单 (Python 3.12-slim)
│   ├── requirements.txt                        # 生产环境干净依赖库声明
│   ├── pyproject.toml                          # 项目元数据与依赖锁信息
│   ├── .env.example                            # 生产环境变量完整模板
│   ├── .gitignore                              # 后端专属忽略文件 (.venv, *.pyc, *.db, 临时日志)
│   └── README.md                               # 后端架构设计与开发运维手册
│
├── Frontend-Blog/                              # 💻 博客前台 (Vue 3 + Vite + ECharts + Element Plus)
│   ├── src/
│   │   ├── api/                                # 前端 HTTP 请求客户端 (article, footprint, comment, rss, music, ...)
│   │   ├── assets/
│   │   │   ├── images/bgc.webp                 # 郁郁葱葱的蓝天大树高清背景图 (Vite 静态哈希 bgc-1CCtb4XF.webp)
│   │   │   └── styles/ali-iconfont.css         # 阿里图标字体样式 (包含 icon-zuji 足迹图标)
│   │   ├── components/
│   │   │   ├── BlogHeader.vue                  # 顶部导航栏 (Kang's Blog 品牌、动态插入「足迹」入口)
│   │   │   ├── BlogFooter.vue                  # 页脚 (© 2026 Kang 版权、备案号与 Sitemap 入口)
│   │   │   ├── HeroBanner.vue                  # 首页顶部大图组件 (绑定大树背景图)
│   │   │   ├── FootprintSplash.vue             # 足迹页面炫酷开屏启航动画
│   │   │   └── SidebarCard.vue                 # 侧边栏站长名片 (头像、在线人数统计、标签、社交媒体)
│   │   ├── view/
│   │   │   ├── Footprint/
│   │   │   │   ├── index.vue                   # 城市足迹地图主页 (ECharts 矢量中国地图、高亮已访问省市)
│   │   │   │   └── CityGallery.vue             # 城市图集画廊 (横向轮播、瀑布流、全屏大图预览走廊)
│   │   │   ├── Article/                        # 文章详情与 Markdown 渲染 (MdPreview)
│   │   │   ├── Archive/                        # 时光轴足迹归档页 (按年月分组)
│   │   │   └── ...                             # Category, Tag, Message, Links, About
│   │   ├── router/index.js                     # 路由守卫 (统一标题后缀 - Kang、足迹开关 use-footprint 拦截)
│   │   └── stores/                             # Pinia 状态树 (theme, visitor, blog)
│   ├── public/
│   │   ├── city/city.json                      # 6.6MB 全国行政区划 GeoJSON 数据 (运行时按需直出，不堵塞首屏)
│   │   └── favicon.ico                         # 站长专属高清头像真 Favicon (925KB)
│   ├── index.html                              # 入口页面 (已注入 no-referrer 防盗链标头与 Kang's Blog 标题)
│   └── vite.config.js                          # Vite 打包配置 (分包与 Terser 压缩优化)
│
├── Frontend-Admin/                             # 🛠️ 管理后台 (Vue 3 + Vite + Pinia + Element Plus)
│   ├── src/
│   │   ├── api/                                # 管理端专用接口客户端 (footprint, article, user, settings, report, ...)
│   │   ├── view/
│   │   │   ├── Footprint/index.vue             # 足迹管理 (省市级联选择、游历日期、图集抽屉、OSS 多图拖拽排序)
│   │   │   ├── Dashboard/index.vue             # 大屏数据仪表盘 (PV 折线图、访客省份饼图、Top 10 热文榜)
│   │   │   ├── Article/                        # 文章编写与审核 (Markdown 编辑器、置顶控制、发布状态筛选)
│   │   │   ├── Music/index.vue                 # 音乐播放列表管理 (OSS 音乐链接、歌词、封面直传)
│   │   │   ├── Settings/index.vue              # 系统全局配置 (备案号、建站日期、use-footprint 开关)
│   │   │   └── ...                             # Comment, Message, Category, Tag, Visitor, ViewRecord, OperationLog
│   │   ├── components/                         # 通用弹窗组件 (EmojiPicker, AiCorrectionDialog 错别字纠错弹窗)
│   │   ├── router/index.js                     # 权限路由守卫 (未登录拦截、401 自动退登)
│   │   └── layout/index.vue                    # 侧边栏布局 (根据 use-footprint 动态渲染「足迹管理」菜单)
│   ├── public/favicon.ico                      # 站长专属高清头像真 Favicon (925KB)
│   └── index.html                              # 入口页面 (注入 no-referrer 与 Kang Admin 标题)
│
├── Frontend-Home/                              # 🌐 门户主站 (Vue 3 + Vite，极致轻量卡片流)
│   ├── src/view/Home/index.vue                 # 个人介绍卡片、社交媒体外链矩阵、动态 ICP/公网备案信息
│   └── public/favicon.ico                      # 站长专属高清头像真 Favicon
│
├── Frontend-Cv/                                # 📄 个人在线简历 (Vue 3 + Vite)
│   ├── src/view/Home/index.vue                 # 技能树展示、教育/工作时间轴、响应式布局、A4 打印优化
│   └── public/favicon.ico                      # 站长专属高清头像真 Favicon
│
├── App/                                        # 📱 移动端管理 App (React Native / Expo 原生跨平台工程)
│   ├── src/
│   │   ├── app/                                # Expo Router 页面驱动 (tabs: 首页仪表盘, 文章列表, 审核中心, 名片设置)
│   │   ├── components/                         # 原生组件库 (CRUD 通用卡片、图片上传组件、主题化文字与容器)
│   │   ├── lib/api-client.ts                   # 移动端 HTTP 通信客户端 (对接生产后台 /admin/* 接口)
│   │   └── constants/theme.ts                  # 移动端明暗自适应主题
│   ├── app.json                                # 跨平台移动端应用配置 (包名、图标、版本号)
│   ├── eas.json                                # EAS Build 云端编译打包配置 (预览版直接生成 APK)
│   └── BUILD.md                                # 移动端构建与运行指南 (支持 Expo Go 极速扫码预览与云打包)
│
├── docker/                                     # 🐳 容器化与运维支持
│   ├── nginx/                                  # Nginx 网关示例配置与反代模板
│   ├── mysql/init/feitwnd.sql                  # 生产数据库完整建库与初始数据 SQL (含 21 张表与足迹初始行)
│   ├── backup.sh                               # 数据库与静态资源每日自动冷备份脚本
│   └── monitor.sh                              # 2C2G 内存与服务存活自动告警巡检脚本
│
├── docker-compose.yml                          # 编排文件 (FastAPI 后端 + MySQL 8 + Redis 7 本地一键启动)
├── TECHNICAL_ARCHITECTURE.md                   # 📐 系统总体技术架构设计蓝图 (架构原则、领域 Seams、ADR 决策日志)
├── ALIYUN_MIGRATION_REPORT.md                  # 📊 阿里云生产环境迁移落地报告 (只读审计基线、内存账本、回滚手册)
├── LICENSE                                     # MIT 开源协议许可声明
└── README.md                                   # 📖 项目主页说明文档
```

---

## 💼 后端 10 大核心业务域（Domain Modules）职责明细

| 模块名称 | 职责边界与对应数据表 | 核心设计细节与亮点 |
| :--- | :--- | :--- |
| **`article`** | 文章创作与归档<br>(`articles`, `article_categories`, `article_tags`, `article_tag_relations`) | 1. **死字段只读推导**：历史表中的 `publish_year/month/day` 均为全 NULL 死字段，归档接口（`get_archive`）由 `publish_time` 在内存中只读计算年月，彻底消除前端 `undefined-null` 异常，且绝不写入数据库脏数据；<br>2. **分类与标签聚合**：文章列表（`PageResult`）自动组装分类徽章与标签数组。 |
| **`footprint`** | 城市足迹与城市图集<br>(`city_footprints`, `city_images`) | 1. **级联物理清理**：批量删除城市足迹时，底层先执行 `DELETE FROM city_images WHERE city_id IN (...)`，保持数据库无孤儿脏数据；<br>2. **图集与大图联动**：支持多图拖拽排序权重（`sort`）与显隐开关控制；博客端按游历日期降序输出。 |
| **`site_content`** | 站点资料与动态配置<br>(`personal_info`, `skills`, `experiences`, `social_media`, `music`, `friend_links`, `system_config`) | 1. **单数据源多端投影**：一份站长个人资料支撑 Blog、Admin、Home、CV 4 个站的不同字段裁剪；<br>2. **序列化穿透修正**：管理端音乐列表 `PageResult.records` 采用 `list[Any]` 宽松声明，彻底根除 Pydantic union 把记录吃成 `{}` 的深层缺陷。 |
| **`comments`** | 互动留言与评论系统<br>(`article_comments`, `messages`) | 1. **两级树状盖楼**：利用 `rootId` 与 `parentId` 在 Service 层一次遍历完成评论盖楼树形组装；<br>2. **内容净化**：Markdown 原文自动净化为 HTML，敏感词过滤，支持悄悄话与博主专属回复。 |
| **`interaction`** | 访客轻互动<br>(`article_likes`) | 1. **幂等防重点赞**：结合 `(article_id, visitor_id)` 唯一索引，重复点赞无痛忽略；<br>2. **参数容错**：未登录或匿名访客调用 `has_liked` 接口时，`visitorId` 空值默认返回 `false`，杜绝 400 校验异常。 |
| **`ops`** | 运维审计与访客分析<br>(`operation_logs`, `views`, `visitors`, `rss_subscriptions`) | 1. **真实公网 IP 还原**：通过 `_real_client_ip()` 提取 Nginx 注入的 `X-Real-IP` 或 `X-Forwarded-For`，彻底清除内部调试用的 `127.0.0.1` 假 IP；<br>2. **输入宽容度**：访客指纹上报支持数字型设备参数，对齐旧系统 Jackson 自动转字符串的行为。 |
| **`report`** | 运营大屏统计分析 | 1. **全链路 SQL 聚合**：通过 SQLAlchemy 聚合查询最近 7 天 PV 趋势折线图、Top 10 热门阅读文章榜、访客 IP 对应省份分布饼图；<br>2. **动态默认日期**：报表 `begin`/`end` 参数缺省时自动回落至最近 7 天区间。 |
| **`auth`** | 管理员认证与安全鉴权<br>(`admin`) | 1. **双重算法平滑过渡**：兼容历史 `sha256(password + salt)`，并按 ADR-009 设计支持渐进升级；<br>2. **会话持久化**：基于 Redis Set 维护 Token 活跃集合（`imcjk:token:active:{adminId}`），TTL 精确对齐原系统的 2 小时（7200000ms）。 |
| **`misc`** | 通用网关与第三方集成 | 1. **OSS 流式直传**：统一文件上传接口（`uploadFile`）采用 `oss2` 直接推送到阿里云 Bucket，免本地落盘；<br>2. **SEO 友好**：动态生成全站 `sitemap.xml` 与标准 XML 格式的 RSS 订阅流。 |
| **`ws`** | 实时通信广播 | 提供 `/api/ws/online` 原生 WebSocket 端点，基于定时心跳与连接池实时统计并广播当前在线访客数。 |

---

## 🗄️ 数据库 21 张物理表模型映射矩阵

```text
feitwnd 数据库 (21 表)
├── 系统核心与鉴权
│   ├── admin                      <──> app.db.models.admin.Admin
│   └── system_config              <──> app.db.models.site_content.SystemConfig
├── 博客与内容创作
│   ├── articles                   <──> app.db.models.article.Article
│   ├── article_categories         <──> app.db.models.article.ArticleCategory
│   ├── article_tags               <──> app.db.models.article.ArticleTag
│   └── article_tag_relations      <──> app.db.models.article.ArticleTagRelation
├── 评论、留言与互动
│   ├── article_comments           <──> app.db.models.engagement.ArticleComment
│   ├── article_likes              <──> app.db.models.engagement.ArticleLike
│   └── messages                   <──> app.db.models.engagement.Message
├── 访客、运维与审计
│   ├── visitors                   <──> app.db.models.engagement.Visitor
│   ├── views                      <──> app.db.models.engagement.View
│   ├── operation_logs             <──> app.db.models.ops.OperationLog
│   └── rss_subscriptions          <──> app.db.models.ops.RssSubscription
├── 站长资料与主页扩展
│   ├── personal_info              <──> app.db.models.site_content.PersonalInfo
│   ├── skills                     <──> app.db.models.site_content.Skill
│   ├── experiences                <──> app.db.models.site_content.Experience
│   ├── social_media               <──> app.db.models.site_content.SocialMedia
│   ├── music                      <──> app.db.models.site_content.Music
│   └── friend_links               <──> app.db.models.site_content.FriendLink
└── 【最新上游同步】城市足迹与图集
    ├── city_footprints            <──> app.db.models.footprint.CityFootprint
    └── city_images                <──> app.db.models.footprint.CityImage
```

---

## 🛡️ 全局通用机制与设计基线保证

1. **请求级事务生命周期（Auto-Commit）**：  
   `core/deps.py` 中的 `get_db_session` 采用 `async with session: try ... yield ... await session.commit() except: await session.rollback()` 模式，确保业务代码**无需手动 commit 即可真实落盘持久化**，发生错误自动回滚脏数据。
2. **统一响应信封（Uniform Envelope）**：  
   全站所有 API 输出统一包装为 `Envelope` 结构体：成功返回 `{code: 1, msg: null, data: ...}`，业务与参数错误返回 `{code: 0, msg: "...", data: null}`。
3. **参数宽容解析（Lenient Binding）**：  
   `core/query.py` 提供的 `LenientQueryModel` 会在 Pydantic 校验前将 URL 中的空字符串 `""` 自动转换为 `None` 或字段默认值，彻底解决旧前端发送 `?page=1&pageSize=15&title=&categoryId=&isPublished=` 时抛出 400 Bad Request 的问题。
4. **防盗链与静态资产防护**：  
   所有前端 HTML 入口均注入 `<meta name="referrer" content="no-referrer">`，配合 Nginx 的 `add_header Referrer-Policy "no-referrer" always;`，确保阿里云 OSS 中的图片与音频免受 Referer 白名单策略拦截。
5. **轻量内存预算（2C2G 保护）**：  
   Uvicorn 锁定单 Worker 进程（`--workers 1`），全后端进程仅占 **104 MB** 物理内存，相比原 Java Spring Boot 节约 240MB+，整机空闲可用内存稳定在 580MB 以上，从根本上杜绝 OOM 死机风险。

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
