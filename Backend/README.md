# IMCJK Blog Backend (Python / FastAPI)

基于 **Python 3.12 + FastAPI + SQLAlchemy 2.0 Async + MySQL 8.0 + Redis 7.2** 构建的现代化全异步博客后端系统。

原系统由 Java / Spring Boot 3 重构而来，100% 保持对外 HTTP/WebSocket 契约与历史数据无损兼容，在阿里云 2C2G 生产环境下长效稳定运行，内存开销较 Java 减少 240MB+。

---

## 🛠️ 技术栈

* **核心框架**：[FastAPI](https://fastapi.tiangolo.com/) (全异步 ASGI) + [Uvicorn](https://www.uvicorn.org/)
* **ORM 与数据库**：[SQLAlchemy 2.0 Async](https://www.sqlalchemy.org/) + [aiomysql](https://github.com/aio-libs/aiomysql) + MySQL 8.0
* **数据校验**：[Pydantic v2](https://docs.pydantic.dev/) + [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
* **缓存与限流**：[Redis 7.2](https://redis.io/) (Token 白名单、令牌桶限流、动态验证码)
* **鉴权安全**：PyJWT (HS512 / HS384 / HS256) + PBKDF2 / SHA256 渐进式密码升级
* **存储与通信**：阿里云 OSS (oss2) 流式直传 + QQ 邮箱 SMTP (SSL 465) + 原生 WebSocket

---

## 📁 目录结构

```text
Backend/
├── app/
│   ├── core/                  # 基础设施 (配置、依赖注入、异常信封、Legacy类型、宽容查询)
│   ├── db/                    # 数据库会话工厂与 21 个物理 ORM 映射模型
│   │   └── models/            # 实体模型 (article, footprint, engagement, site_content, admin, ops)
│   ├── integrations/          # 外部服务适配器 (阿里云 OSS, Redis 缓存, SMTP 邮件)
│   ├── modules/               # 领域业务模块 (Router -> Service -> Repository)
│   │   ├── article/           # 文章 CRUD、分类标签、全文搜索、时间轴归档
│   │   ├── auth/              # 管理员认证、动态邮箱验证码、JWT 会话
│   │   ├── comments/          # 文章评论、全站留言板、两级树状盖楼
│   │   ├── footprint/         # 城市足迹、ECharts 矢量地图联动、城市图集画廊
│   │   ├── interaction/       # 访客文章点赞 (唯一防重)
│   │   ├── misc/              # 健康检查、统一 OSS 文件上传、Sitemap、RSS Feed
│   │   ├── ops/               # 真实公网 IP 还原、访客指纹统计、RSS 订阅推送
│   │   ├── report/            # 仪表盘总览、PV 趋势折线图、Top10 热文、省份分布
│   │   ├── site_content/      # 4 端个人信息投影、音乐播放列表、系统扩展配置
│   │   └── taxonomy/          # 分类与标签字典树维护
│   ├── ws/                    # WebSocket (/api/ws/online 实时在线人数广播)
│   └── main.py                # 应用装配工厂 (中间件、异常处理、路由挂载)
├── Dockerfile                 # 容器构建镜像定义
├── requirements.txt           # 生产纯净依赖清单
├── pyproject.toml             # 项目元信息
└── .env.example               # 生产环境变量配置模板
```

---

## 🚀 快速启动

### 1. 本地虚拟环境运行

```bash
# 1. 创建并激活 Python 3.12 虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
# Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 中的 MySQL、Redis、JWT 与 OSS 凭据

# 4. 启动后端开发服务
uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload
```

访问健康检查端点：`http://127.0.0.1:8082/api/health` ➔ 返回 `{"code":1, "msg":null, "data":"Server is running"}`。

### 2. Docker 容器化运行

```bash
docker build -t imcjk-backend:latest .
docker run -d --name imcjk-backend -p 8082:8082 --env-file .env imcjk-backend:latest
```

---

## 🛡️ 核心架构与兼容性设计

1. **统一信封响应**：所有 200 响应统一封装为 `{code: 1, msg: null, data: ...}`，业务异常映射为 `{code: 0, msg: "...", data: null}`。
2. **CamelModel 驼峰直出**：Pydantic 序列化器自动将 Python 的 `snake_case` 映射为前端期望的 `camelCase`。
3. **LenientQueryModel 宽容绑定**：对齐 Spring MVC 处理 URL 空查询串行为，将形如 `?page=1&title=&categoryId=&isPublished=` 中的空字符串自动转为 `None` / 默认值，彻底消除 400 校验异常。
4. **请求级自动事务**：`deps.get_db_session` 采用 `try...yield...commit` 闭环，路由无异常退出自动落盘，出现未捕获异常自动回滚。
