"""FastAPI 应用装配 —— 等价于旧 ``WebMvcConfiguration`` + ``Spring Boot`` 启动装配。

本文件把 Phase 2 Stage 2.1 已实现的层装配成一个可运行应用，并**逐一复刻**旧系统的
Web 层横切行为。所有复刻点都在下方标注了【FACT】来源。

Stage 2.2 追加装配：``taxonomy``（11 端点）+ ``interaction``（3 端点）
—— 覆盖矩阵见 ``docs/PHASE2_STAGE2_2_SCOPE.md``，共 14 条 path。

复刻清单（对照 ``cc/feitwnd/config/WebMvcConfiguration.java``）::

  1. 拦截器        addInterceptor(jwtTokenAdminInterceptor).addPathPatterns("/admin/**")
                   .excludePathPatterns("/admin/admin/login", "/admin/admin/sendCode",
                                        "/admin/admin/logout")
                   → 由 ``app.core.deps.get_current_admin`` 在**路由级**复刻
                     （FastAPI 无全局拦截器；挂在 ``/admin/**`` 的端点上，
                      白名单端点不挂。见 ``modules/auth/router.py``）

  2. 缓存头拦截器  addInterceptor(noCache).addPathPatterns("/admin/**","/blog/**","/cv/**","/home/**")
                   → ``NoCacheMiddleware``（**注意：无 excludePathPatterns**，
                     因此 ``/admin/admin/login`` **也**带 no-cache 头）
                   → ``/health`` **不在**列表内 → 不带这些头

  3. CORS          addMapping("/**")
                   .allowedOriginPatterns("*").allowedMethods(GET,POST,PUT,DELETE,OPTIONS)
                   .allowedHeaders("*").allowCredentials(true).maxAge(3600)
                   → ``CORSMiddleware``（⚠️ 必须用 ``allow_origin_regex`` —— 见下方注释）

  4. 消息转换器    extendMessageConverters → JacksonObjectMapper 插到第 0 位
                   → 日期格式 ``LegacyDateTime/LegacyDate/LegacyTime``（``core/legacy_types.py``）
                     + ``LegacyJSONResponse``（``ensure_ascii=False``）

  5. 全局异常      → ``core/errors.register_exception_handlers``

  6. 路径前缀      【DECISION·ADR-010 决策一】新后端**自带** ``/api`` 前缀
                   （旧系统由 Nginx 剥离）⇒ **对外可见路径逐字不变**
                   （旧外部 ``/api/admin/admin/login`` == 新 ``{prefix}/admin/admin/login``）
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import Settings, get_settings
from app.core.errors import LegacyJSONResponse, register_exception_handlers
from app.core.logging import setup_logging
from app.modules.article.router import router as article_router
from app.modules.auth.router import router as auth_router
from app.modules.interaction.router import router as interaction_router
from app.modules.ops.router import admin_router as ops_admin_router, router as ops_router
from app.modules.comments.router import admin_router as comments_admin_router, router as comments_router
from app.modules.report.router import admin_router as report_admin_router
from app.modules.article.router import admin_router as article_admin_router, router as article_router
from app.modules.misc.router import router as misc_router
from app.modules.site_content.router import router as site_content_router
from app.modules.site_content.admin_router import router as site_content_admin_router
from app.modules.taxonomy.router import router as taxonomy_router
from app.modules.footprint import admin_router as footprint_admin_router, blog_router as footprint_blog_router
from app.ws.router import router as ws_router

__all__ = ["create_app", "app", "LEGACY_NO_CACHE_PATTERNS", "no_cache_path_prefixes"]

# 【FACT】``WebMvcConfiguration`` 中 no-cache 拦截器的 addPathPatterns 逐字复制
#         ⚠️ 该拦截器**没有** excludePathPatterns → 白名单端点（如 /admin/admin/login）同样带头
LEGACY_NO_CACHE_PATTERNS: tuple[str, ...] = ("/admin", "/blog", "/cv", "/home")

# 【FACT】``response.setHeader(...)`` 逐字复制
_NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
}


def no_cache_path_prefixes(api_prefix: str) -> tuple[str, ...]:
    """把旧的内部路径模式映射为**新系统实际看到的路径**。

    【FACT】旧系统里该拦截器匹配的是**后端内部路径**（``/blog/**``），
    因为 Nginx 已经把 ``/api`` 前缀剥掉了（``proxy_pass .../``）。

    【DECISION·ADR-010 决策一】新后端**自带** ``/api`` 前缀、Nginx 改为透传
    ⇒ 后端现在看到的路径是 ``/api/blog/...``。
    ⇒ **同一份对外可见路径**（``/api/blog/...``）在两种拓扑下都必须带 no-cache 头，
      因此这里匹配的是 ``{api_prefix}`` + 旧模式。

    ``api_prefix`` 为空串时退化为裸模式（等价于旧内部路径）。
    """
    return tuple(f"{api_prefix}{p}" for p in LEGACY_NO_CACHE_PATTERNS)


class NoCacheMiddleware(BaseHTTPMiddleware):
    """复刻旧系统第 2 个拦截器的响应头写入。

    【FACT】Spring ``addPathPatterns`` 使用 Ant/PathPattern 语义，``"/admin/**"``
    **同时匹配** ``/admin`` 与 ``/admin/...``（``/**`` 可匹配 0 个或多个段）。
    因此这里用 ``path == prefix or path.startswith(prefix + "/")`` 精确对齐，
    而不是简单地 ``startswith(prefix)``（那会误伤 ``/administration``）。
    """

    def __init__(self, app, prefixes: tuple[str, ...]) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._prefixes = prefixes

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        response = await call_next(request)
        path = request.url.path
        for prefix in self._prefixes:
            if path == prefix or path.startswith(prefix + "/"):
                for key, value in _NO_CACHE_HEADERS.items():
                    response.headers[key] = value
                break
        return response


def _cors_middleware_options() -> dict[str, object]:
    """旧 CORS 配置的等价映射。

    ⚠️ **关键**：旧系统用 ``allowedOriginPatterns("*")`` + ``allowCredentials(true)``。
       语义 = **回显请求的 Origin**（而不是返回 ``*``）——
       因为浏览器禁止 ``Access-Control-Allow-Origin: *`` 与凭据同用。

       Starlette 的 ``allow_origins=["*"]`` 在**没有 Cookie/凭据**时返回 ``*``，
       只有带凭据时才回显 → **不等价**。
       ⇒ 因此这里用 ``allow_origins=[]`` + ``allow_origin_regex=".*"``，
         使**任何** Origin 都被回显，逐字对齐 ``allowedOriginPatterns("*")``。
    """
    return {
        "allow_origins": [],
        "allow_origin_regex": ".*",
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["*"],
        "max_age": 3600,
    }


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """启动 / 关闭钩子。

    Phase 2.1 **不建立数据库/Redis 连接**：
      * 旧系统启动时会初始化连接池，但本阶段处于「新旧并行、旧系统仍在服务」状态，
        主动连接会带来无收益的耦合与失败面；
      * 契约测试通过 ``app.dependency_overrides`` 注入替身，
        **不需要**真实基础设施（本轮指令 §29：不得连生产）。
    """
    settings: Settings = app.state.settings
    setup_logging(settings.log.level)
    from app.core.logging import get_logger

    get_logger(__name__).info(
        "应用启动：name=%s env=%s api_prefix=%s（未连接 DB / Redis）",
        settings.app.name,
        settings.app.env,
        settings.app.api_prefix,
    )
    yield
    get_logger(__name__).info("应用关闭")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log.level)

    app = FastAPI(
        title=settings.app.name,
        version="0.1.0",
        lifespan=_lifespan,
        # 【FACT】``extendMessageConverters`` 把 Jackson 映射器插到第 0 位
        # → 所有响应都走该序列化器 ⇒ 这里把 ``LegacyJSONResponse`` 设为**默认**响应类
        default_response_class=LegacyJSONResponse,
        # 本阶段不生成 ``/docs`` 之类的额外端点吗？—— 保留（仅开发可见，属 FastAPI 内置，
        # 不影响任何旧路径；若生产需要可在部署层关闭）。
    )
    app.state.settings = settings

    # --- 5) 全局异常处理器（顺序无关）-------------------------------------
    register_exception_handlers(app)

    # --- 3) CORS -----------------------------------------------------------
    app.add_middleware(CORSMiddleware, **_cors_middleware_options())  # type: ignore[arg-type]

    # --- 2) no-cache 响应头 ------------------------------------------------
    # ⚠️ 后 add 的中间件在更外层。CORS 需最外层以便处理预检请求（OPTIONS 短路）。
    app.add_middleware(NoCacheMiddleware, prefixes=no_cache_path_prefixes(settings.app.api_prefix))

    # --- 6) 路由挂载（【DECISION·ADR-010】自带 /api 前缀）------------------
    prefix = settings.app.api_prefix
    app.include_router(auth_router, prefix=prefix)
    app.include_router(article_router, prefix=prefix)
    app.include_router(article_admin_router, prefix=prefix + '/admin')
    app.include_router(misc_router, prefix=prefix)
    app.include_router(site_content_router, prefix=prefix)
    app.include_router(site_content_admin_router, prefix=prefix + "/admin")
    app.include_router(taxonomy_router, prefix=prefix)
    app.include_router(interaction_router, prefix=prefix)
    app.include_router(ops_admin_router, prefix=prefix + '/admin')
    app.include_router(ops_router, prefix=prefix)
    app.include_router(comments_admin_router, prefix=prefix + '/admin')
    app.include_router(comments_router, prefix=prefix)
    app.include_router(report_admin_router, prefix=prefix + '/admin')
    app.include_router(footprint_admin_router, prefix=prefix + '/admin')
    app.include_router(footprint_blog_router, prefix=prefix)
    app.include_router(ws_router, prefix=prefix)

    # --- A119 GET /health（``common/HealthController``）--------------------
    @app.get(f"{prefix}/health", response_model=None, tags=["common"], summary="健康检查")
    async def health() -> LegacyJSONResponse:
        """【FACT】``HealthController.health()`` → ``Result.success("Server is running")``

        ⇒ ``{code:1, msg:null, data:"Server is running"}``

        ⚠️ ``/health`` **不在** no-cache 拦截器的 ``addPathPatterns`` 中
           → 响应**不带** ``Cache-Control`` / ``Pragma``。

        ⚠️ 该端点也在任何鉴权之外（旧系统拦截器只挂 ``/admin/**``）。
        """
        return LegacyJSONResponse(
            status_code=200,
            content={"code": 1, "msg": None, "data": "Server is running"},
        )

    return app


app = create_app()
